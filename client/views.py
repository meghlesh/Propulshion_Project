from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.contrib.messages import get_messages
from django.db.models import Sum

from .models import (
    ClientProfile,
    Project,
    ProjectDocument,
    PersonalDocument,
    Payment,
    PaymentRequest,
)


# ===========================
# CLIENT LOGIN
# ===========================
from django.contrib.messages import get_messages

def client_login(request):

    # CLEAR ALL MESSAGES ON EVERY GET request
    if request.method == "GET":
        storage = get_messages(request)
        list(storage)  # force message consumption

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(username=email, password=password)
        if user:
            login(request, user)
            return redirect("client:client_dashboard")

        messages.error(request, "Invalid email or password")
        return redirect("client:client_login")

    return render(request, "client/client_login.html")

# ===========================
# CLIENT DASHBOARD
# ===========================
@login_required(login_url="client:client_login")
def client_dashboard(request):
    user = request.user
    client = getattr(user, "client_profile", None)
    welcome_name = client.name if client and client.name else user.username
    # Safety: if somehow user has no client profile
    if not client:
        return render(request, "client/client_dashboard.html", {
            "user": user,
            "client": None,
            "total_projects": 0,
            "completed_projects": 0,
            "ongoing_projects": 0,
            "pending_review": 0,
            "approved_requests": 0,
            "pending_percent": 0,
            "completed_percent": 0,
            "total_revenue": 0,
            "total_invoiced": 0,
            "total_paid": 0,
            "pending_payment": 0,
            "recent_projects": [],
        })

    # All projects of this client
    projects = Project.objects.filter(client=client)

    # Project counts
    total_projects = projects.count()
    completed_projects = projects.filter(status="Completed").count()
    ongoing_projects = projects.filter(status="In Progress").count()

    # Task status using payment requests as "tasks"
    pending_review = PaymentRequest.objects.filter(
        client=client, status="Pending"
    ).count()
    approved_requests = PaymentRequest.objects.filter(
        client=client, status="Approved"
    ).count()

    total_tasks = pending_review + approved_requests
    if total_tasks > 0:
        pending_percent = int(pending_review / total_tasks * 100)
        completed_percent = int(approved_requests / total_tasks * 100)
    else:
        pending_percent = 0
        completed_percent = 0

    # Revenue stats from Payment model
    payments = Payment.objects.filter(project__client=client)  
    totals = payments.aggregate(
        total_amount=Sum("amount_total"),
        total_paid=Sum("amount_paid"),
        total_balance=Sum("balance_amount"),
    )

    total_invoiced = totals["total_amount"] or 0
    total_paid = totals["total_paid"] or 0
    pending_payment = totals["total_balance"] or 0

    # Big number on card – total revenue
    total_revenue = total_invoiced

    # Recent activity: latest projects for this client
    recent_projects = projects.order_by("-start_date")[:5]

    context = {
        "user": user,
        "client": client,
        "welcome_name": welcome_name,
        # Project metrics
        "total_projects": total_projects,
        "completed_projects": completed_projects,
        "ongoing_projects": ongoing_projects,

        # Task / request status
        "pending_review": pending_review,
        "approved_requests": approved_requests,
        "pending_percent": pending_percent,
        "completed_percent": completed_percent,

        # Revenue
        "total_revenue": total_revenue,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "pending_payment": pending_payment,

        # Recent activity
        "recent_projects": recent_projects,
    }

    return render(request, "client/client_dashboard.html", context)


# ===========================
# PROJECT LIST
# ===========================
@login_required(login_url="client:client_login")
def client_projects(request):
    client = request.user.client_profile
    projects = Project.objects.filter(client=client)
    return render(request, "client/client_projects.html", {"projects": projects})


# ===========================
# PROJECT DETAILS
# ===========================
@login_required(login_url="client:client_login")
def client_project_details(request, project_id):
    client = request.user.client_profile
    project = get_object_or_404(Project, id=project_id, client=client)

    documents = ProjectDocument.objects.filter(project=project).order_by("-uploaded_at")
    payments = Payment.objects.filter(project=project).order_by("payment_date")

    totals = payments.aggregate(
        total_amount=Sum("amount_total"),
        total_paid=Sum("amount_paid"),
        total_balance=Sum("balance_amount"),
    )

    context = {
        "project": project,
        "documents": documents,
        "payments": payments,
        "total_amount": totals["total_amount"] or 0,
        "paid_amount": totals["total_paid"] or 0,
        "balance_amount": totals["total_balance"] or 0,
        "progress": 100 if project.status == "Completed" else 60 if project.status == "In Progress" else 20,
        "tasks": []
    }

    return render(request, "client/client_project_details.html", context)


# ===========================
# UPLOAD PROJECT DOCUMENT
# ===========================
@login_required(login_url="client:client_login")
def upload_project_document(request, project_id):
    client = request.user.client_profile
    project = get_object_or_404(Project, id=project_id, client=client)

    if request.method == "POST":
        file = request.FILES.get("attachment")

        if not file:
            messages.error(request, "Please select a file.")
            return redirect("client:client_project_details", project_id=project_id)

        # File type validation
        ext = file.name.split(".")[-1].lower()
        allowed_ext = ["jpg", "jpeg", "png", "pdf", "docx"]

        if ext not in allowed_ext:
            messages.error(request, "Only JPG, JPEG, PNG, PDF, DOCX files are allowed.")
            return redirect("client:client_project_details", project_id=project_id)

        # 10MB = 10 * 1024 * 1024
        if file.size > 10 * 1024 * 1024:
            messages.error(request, "File size cannot exceed 10 MB.")
            return redirect("client:client_project_details", project_id=project_id)

        # SAVE AS PENDING DOCUMENT
        ProjectDocument.objects.create(
            project=project,
            attachment=file,
            uploaded_by="client",
            status="pending",
        )

        messages.success(request, "Document uploaded. Waiting for admin approval.")

    return redirect("client:client_project_details", project_id=project_id)


# ===========================
# PERSONAL DOCUMENT LIST
# ===========================
@login_required(login_url="client:client_login")
def client_personal_documents(request):
    client = request.user.client_profile
    documents = PersonalDocument.objects.filter(client=client).order_by('-id')

    # Calculate total size used
    total_bytes = sum(doc.attachment.size for doc in documents if doc.attachment)
    total_mb = total_bytes / (1024 * 1024)
    total_limit_mb = 100
    
    # Calculate percentage
    usage_percentage = (total_mb / total_limit_mb) * 100 if total_limit_mb > 0 else 0

    return render(request, "client/client_personal_documents.html", {
        "documents": documents,
        "user": request.user,
        "total_usage_mb": round(total_mb, 2),
        "total_limit_mb": total_limit_mb,
        "usage_percentage": min(usage_percentage, 100),
    })


# ===========================
# UPLOAD PERSONAL DOCUMENT
# ===========================
@login_required(login_url="client:client_login")
def upload_personal_document(request):
    client = request.user.client_profile

    if request.method == "POST":
        file = request.FILES.get("attachment")

        if not file:
            messages.error(request, "Please select a file.")
            return redirect("client:client_personal_documents")

        ext = file.name.split(".")[-1].lower()
        allowed_ext = ["pdf", "docx", "jpg", "jpeg", "png"]

        if ext not in allowed_ext:
            messages.error(request, "Only PDF, DOCX, JPG, JPEG, PNG allowed.")
            return redirect("client:client_personal_documents")

        # 1. INDIVIDUAL FILE LIMIT (10 MB)
        max_file_size_mb = 10
        if file.size > max_file_size_mb * 1024 * 1024:
            messages.error(request, f"File size cannot exceed {max_file_size_mb} MB.")
            return redirect("client:client_personal_documents")

        # 2. TOTAL STORAGE LIMIT CHECK (100 MB)
        max_total_storage_mb = 100
        current_documents = PersonalDocument.objects.filter(client=client)
        current_total_bytes = sum(doc.attachment.size for doc in current_documents if doc.attachment)
        
        # Check if adding this new file exceeds the total limit
        if (current_total_bytes + file.size) > max_total_storage_mb * 1024 * 1024:
            current_mb = round(current_total_bytes / (1024 * 1024), 2)
            messages.error(
                request, 
                f"Storage limit reached! You are using {current_mb} MB of {max_total_storage_mb} MB. "
                "Please delete old documents to upload new ones."
            )
            return redirect("client:client_personal_documents")

        PersonalDocument.objects.create(client=client, attachment=file)
        messages.success(request, "Document uploaded successfully.")

    return redirect("client:client_personal_documents")


# DELETE PERSONAL DOCUMENT
@login_required(login_url="client:client_login")
def delete_personal_document(request, doc_id):
    client = request.user.client_profile
    doc = get_object_or_404(PersonalDocument, id=doc_id, client=client)

    doc.attachment.delete(save=False)
    doc.delete()

    messages.success(request, "Document deleted successfully.")
    return redirect("client:client_personal_documents")



@login_required(login_url="client:client_login")
def client_payments(request):
    client = request.user.client_profile

    # All projects of this client
    projects = Project.objects.filter(client=client)

    # Build project payment summary list
    project_list = []

    for project in projects:
        payment_summary = Payment.objects.filter(project=project).first()

        project_list.append({
            "project": project,
            "total": payment_summary.amount_total if payment_summary else 0,
            "paid": payment_summary.amount_paid if payment_summary else 0,
            "pending": payment_summary.balance_amount if payment_summary else 0,
        })

    context = {
        "project_list": project_list,
    }

    return render(request, "client/client_payments.html", context)



@login_required(login_url="client:client_login")
def client_project_payments(request, project_id):
    client = request.user.client_profile
    project = get_object_or_404(Project, id=project_id, client=client)

    payment_summary = Payment.objects.filter(project=project).first()

    total_amount = payment_summary.amount_total if payment_summary else 0
    paid_amount = payment_summary.amount_paid if payment_summary else 0
    balance_amount = payment_summary.balance_amount if payment_summary else total_amount
    existing_payment = Payment.objects.filter(project=project).last()

    # FIXED: Show ALL history (client + admin)
    history = PaymentRequest.objects.filter(
        project=project
    ).order_by("-created_at")

    context = {
        "project": project,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "balance_amount": balance_amount,
        "history": history,
        "existing_payment": existing_payment,
    }
    return render(request, "client/client_project_payments.html", context)



@login_required(login_url="client:client_login")
@require_POST
def client_make_payment(request, project_id):
    client = request.user.client_profile
    project = get_object_or_404(Project, id=project_id, client=client)

    amount = request.POST.get("amount")
    mode = request.POST.get("mode")
    transaction_id = request.POST.get("transaction_id")
    note = request.POST.get("note")
    screenshot = request.FILES.get("screenshot")

    # 1. VALIDATION: Check if amount and mode are present
    if not amount or not mode:
        messages.error(request, "Please enter amount and select payment mode.")
        return redirect("client:client_project_payments", project_id=project.id)

    # 2. VALIDATION: Make screenshot MANDATORY
    if not screenshot:
        messages.error(request, "Payment proof (screenshot) is required.")
        return redirect("client:client_project_payments", project_id=project.id)

    # 3. VALIDATION: Screenshot constraints (Only runs if screenshot exists)
    # Check Extension
    ext = screenshot.name.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png"]:
        messages.error(request, "Only JPG, JPEG, PNG files allowed for payment proof.")
        return redirect("client:client_project_payments", project_id=project.id)

    # Check Size
    if screenshot.size > 5 * 1024 * 1024:  # 5 MB
        messages.error(request, "Screenshot size cannot exceed 5 MB.")
        return redirect("client:client_project_payments", project_id=project.id)

    try:
        amount = float(amount)
    except ValueError:
        messages.error(request, "Invalid amount.")
        return redirect("client:client_project_payments", project_id=project.id)

    # Create PaymentRequest
    pr = PaymentRequest.objects.create(
        project=project,
        client=client,
        amount=amount,
        mode=mode,
        transaction_id=transaction_id,
        note=note,
        status="Pending",
        screenshot=screenshot  # Save the file (it's mandatory now)
    )

    messages.success(
        request,
        "Your payment request has been sent to admin. Screenshot uploaded."
    )
    return redirect("client:client_project_payments", project_id=project.id)


def client_detail(request, client_id):
    client = get_object_or_404(ClientProfile, id=client_id)

    # Calculate amounts safely
    total_amount = client.total_amount or 0
    paid_amount = client.paid_amount or 0
    remaining_amount = total_amount - paid_amount

    # Auto-update payment status
    if remaining_amount <= 0:
        client.payment_status = "Paid"
    elif paid_amount > 0:
        client.payment_status = "Pending"
    else:
        client.payment_status = "Overdue"

    client.save()

    return render(request, "client_detail.html", {
        "client": client,
        "remaining_amount": remaining_amount,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
    })

@login_required(login_url='client:client_login')
def client_logout(request):
    logout(request)
    return redirect('home')




@login_required(login_url="client:client_login")
def upload_payment_proof(request, project_id):
    project = get_object_or_404(Project, id=project_id, client=request.user.client_profile)

    payment = Payment.objects.filter(project=project).first()

    if request.method == "POST":
        screenshot = request.FILES.get("screenshot")

        if screenshot:
            payment.screenshot = screenshot
            payment.save()

            messages.success(request, "Payment proof uploaded successfully!")
        else:
            messages.error(request, "Please upload a valid image.")

        return redirect("client:client_payments")  # back to payment list

    return redirect("client:client_payments")