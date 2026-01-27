from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.db.models import Sum
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from client.models import Project, ProjectDocument, ClientProfile, Payment
from .forms import AssignProjectForm
from client.models import ProjectDocument, Payment, PaymentRequest, Payment, Project
import logging
from website.utils import send_expert_rejection_email, send_expert_accept_email
import os
import mimetypes
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import JobApplication  # adjust import if needed
import os
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetConfirmView
from django.utils.crypto import get_random_string
from django.contrib.auth import views as auth_views
from django.utils.http import urlsafe_base64_decode
from django.views.generic import FormView
from django.utils.encoding import force_str
from django.urls import reverse_lazy
import re
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from website.utils import expert_token_generator
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib import messages
from .models import Expert
from django import forms
import pytz
import logging
from django.urls import reverse_lazy
from django.utils.timezone import timedelta
from django.http import JsonResponse
from .models import JobApplication
from website.utils import verify_otp, resend_otp
from django.utils.text import slugify
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from datetime import datetime
from django.db.models import Q 
from cryptography.fernet import Fernet
from django.db import transaction 
from .models import Service, ContactMessage, ScheduleDemo, Job, JobApplication, ExpertQuery, BlogPost, Expert, CandidateProfile, AboutUs, CompanyValue, TeamMember, Mission, PrivacyPolicy, TermsAndConditions, Portfolio, ClientFeedback, ChatbotQA

from .forms import (
    ScheduleDemoForm,
    JobApplicationForm,
    CandidateRegisterForm,
    CandidateLoginForm,
    ExpertQueryForm,
    OTPVerificationForm,
    AboutUsForm,  
    MissionForm,
    PrivacyPolicyForm, 
    TermsAndConditionsForm,
    ContactMessageForm,
    ClientFeedbackForm,
)
import random 
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse 
from django.contrib.auth.hashers import make_password, check_password 
import json
from .utils import encrypt_data, decrypt_data
from .forms import ContactMessageForm
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from website.utils import expert_token_generator
from django.template.loader import render_to_string
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render
from .models import Service  





def send_confirmation_email(recipient_email, user_name, submission_type, details, template_name='website/confirmation_email.html', cta_url=None, extra_context=None):
    """
    Renders and sends a beautiful HTML confirmation email using a specified template.
    Returns True on success, False on failure.
    """
    subject = f"Confirmation: Your {submission_type} Submission to Propulsion Technology"
    
    if "Declined" in submission_type or "Rejected" in submission_type:
        subject = f"Update: Your {submission_type.replace(' (Declined)', '').replace(' (Rejected)', '')} Request Status"

    context = {
        'user_name': user_name,
        'submission_type': submission_type,
        'details': details,
        'site_url': cta_url if cta_url else settings.DEFAULT_SITE_URL,
    }
    if extra_context:
        context.update(extra_context)

    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Confirmation email sent successfully to {recipient_email} using {template_name}.")
        return True
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")
        return False


#  OTP HELPER FUNCTION 
def generate_and_send_otp(model_instance, recipient_email, user_name, user_role):
    """Generates a 6-digit OTP, saves it to the model, and sends it via email."""
    otp_code = str(random.randint(100000, 999999))
    
    model_instance.otp_code = otp_code
    model_instance.otp_created_at = timezone.now()
    model_instance.save()

    subject = f"Your Propulsion Technology {user_role} Verification Code"
    
    context = {
        'user_name': user_name,
        'user_role': user_role,
        'otp_code': otp_code,
    }

    html_message = render_to_string('website/otp_email.html', context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"OTP email sent successfully to {recipient_email} for {user_role}.")
        return True
    except Exception as e:
        print(f"Error sending OTP email to {recipient_email}: {e}")
        return False


#  FILTER HELPER FUNCTION
def filter_queries(request, query_set):
    """Applies date/order filters to a given ExpertQuery queryset."""
    query_set = query_set.select_related('service', 'assigned_expert')
    
    date_filter = request.GET.get('date_filter')
    if date_filter == 'today':
        query_set = query_set.filter(submitted_at__date=timezone.now().date())
    elif date_filter == 'last_7_days':
        one_week_ago = timezone.now() - timezone.timedelta(days=7)
        query_set = query_set.filter(submitted_at__gte=one_week_ago)
    elif date_filter == 'this_month':
        query_set = query_set.filter(submitted_at__year=timezone.now().year, submitted_at__month=timezone.now().month)

    sort_by = request.GET.get('sort_by', 'latest')
    if sort_by == 'oldest':
        query_set = query_set.order_by('submitted_at')
    else: 
        query_set = query_set.order_by('-submitted_at')

    return query_set

#  HOME PAGE 
def home(request):
    form = ContactMessageForm()

    if request.user.is_authenticated and not request.user.is_staff:
        pass  

    services = Service.objects.all().order_by('order')
    portfolios = Portfolio.objects.all().order_by('order')
    latest_posts = BlogPost.objects.filter(status='published').order_by('-published_date')
    feedbacks = ClientFeedback.objects.all().order_by('-created_at')

    return render(request, 'website/index.html', {
        'services': services,
        'latest_posts': latest_posts,
        'portfolios': portfolios,
        'contact_form': form,  
        'feedbacks': feedbacks,
        'user': request.user if request.user.is_authenticated else None,
    })

#  CONTACT FORM 

def contact_submit(request):
    if request.method == "POST":
        form = ContactMessageForm(request.POST, request.FILES)

        # Detect AJAX once
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            contact = form.save()

            # Timezone conversion
            local_tz = pytz.timezone(getattr(settings, "TIME_ZONE", "Asia/Kolkata"))
            local_time = timezone.now().astimezone(local_tz)

            details = {
                "Name": contact.name,
                "Email": contact.email,
                "Subject": contact.subject,
                "Message Snippet": (contact.message[:50] + "...") if len(contact.message) > 50 else contact.message,
                "Submitted On": local_time.strftime("%Y-%m-%d %I:%M %p (%Z)"),
            }

            # Send confirmation email
            try:
                send_confirmation_email(contact.email, contact.name, "Contact Message", details)
            except Exception as e:
                print("Email send failed:", e)

            # ----------------------------
            # AJAX RESPONSE (STOP HERE)
            # ----------------------------
            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "attachment_url": contact.attachment.url if contact.attachment else None
                })

            # Web form fallback
            messages.success(request, "Your message has been sent successfully!")
            return redirect("home")

        # ----------------------------
        # INVALID FORM
        # ----------------------------
        if is_ajax:
            return JsonResponse({
                "success": False,
                "errors": form.errors
            })

        messages.error(request, "Please correct the errors in the contact form.")
        return render(request, "home.html", {"contact_form": form})

    return JsonResponse({"success": False, "error": "Invalid request"})


#  ADMIN LOGIN 
def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Username length validation
        if len(username) < 4 or len(username) > 30:
            messages.error(request, 'Username must be between 4 and 15 characters long.')
            return redirect('admin_login')

        # Password max length validation
        if len(password) > 100:
            messages.error(request, 'Password is too long.')
            return redirect('admin_login')
        
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, 'website/admin_login.html', {
                'error': 'Invalid credentials or not authorized as admin.'
            })
    
    return render(request, 'website/admin_login.html')


#  ADMIN DASHBOARD  
@login_required(login_url='admin_login')
def admin_dashboard(request):
    services = Service.objects.all().order_by('order')
    contact_messages = ContactMessage.objects.all().order_by('-id')[:5]
    demo_count = ScheduleDemo.objects.count()
    draft_count = BlogPost.objects.filter(status='draft').count()

    total_assigned_queries = ExpertQuery.objects.filter(status='assigned').count()
    total_declined_queries = ExpertQuery.objects.filter(status='declined').count()


    return render(request, 'website/admin_dashboard.html', {
        'services': services,
        'contact_messages': contact_messages,
        'demo_count': demo_count,
        'draft_count': draft_count,
        'total_assigned_queries': total_assigned_queries, 
        'total_declined_queries': total_declined_queries, 
    })


#  ADMIN LOGOUT 

@login_required(login_url='admin_login')
def admin_logout(request):
    # Clear all Django messages before logout
    storage = get_messages(request)
    list(storage)  # force message deletion

    logout(request)
    return redirect('home')


#  MANAGE SERVICES 
@login_required(login_url='admin_login')
def manage_services(request):
    services = Service.objects.all().order_by('order')

    # Limits
    TITLE_LIMIT = 40
    SHORT_DESC_LIMIT = 100   
    FULL_DESC_LIMIT = 250

    
    form_values = {
        'title': '',
        'description': '',
        'full_description': '',
        'color': 'accent-green',
        'icon': '',
        'order': 0,
    }

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        full_description = (request.POST.get('full_description') or '').strip()
        color = request.POST.get('color') or 'accent-green'
        icon = (request.POST.get('icon') or '').strip()
        order = request.POST.get('order', 0)
        try:
            order = int(order)
            if order < 0:
                order = 0
        except Exception:
            order = 0

        image = request.FILES.get('image')
        slug_value = slugify(title) if title else ''

        form_values.update({
            'title': title,
            'description': description,
            'full_description': full_description,
            'color': color,
            'icon': icon,
            'order': order,
        })

        errors = []

        if not title:
            errors.append("Title is required.")
        elif len(title) > TITLE_LIMIT:
            errors.append(f"Title cannot exceed {TITLE_LIMIT} characters (you entered {len(title)}).")

        if description and len(description) > SHORT_DESC_LIMIT:
            errors.append(f"Short description cannot exceed {SHORT_DESC_LIMIT} characters (you entered {len(description)}).")

        if full_description and len(full_description) > FULL_DESC_LIMIT:
            errors.append(f"Full description cannot exceed {FULL_DESC_LIMIT} characters (you entered {len(full_description)}).")

        if icon:
            if len(icon) != 1:
                errors.append("Icon must be exactly one character (emoji or single glyph).")

    
        if image:
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            file_ext = image.name.split('.')[-1].lower()
            max_size = 5 * 1024 * 1024 

            if file_ext not in allowed_extensions:
                errors.append("Invalid file type. Only JPG, JPEG, PNG, or GIF files are allowed.")

            if image.size > max_size:
                errors.append("File too large. Maximum size allowed is 5 MB.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'website/manage_services.html', {
                'services': services,
                'form_values': form_values
            })

        Service.objects.create(
            title=title,
            description=description,
            full_description=full_description,
            color=color,
            icon=icon or None,
            order=order,
            slug=slug_value,
            image=image
        )
        messages.success(request, 'New service added successfully!')
        return redirect('manage_services')

    return render(request, 'website/manage_services.html', {
        'services': services,
        'form_values': form_values
    })



def services(request):
    services = Service.objects.all().order_by('order')  
    return render(request, "website/services.html", {"services": services})

def base_context(request):
    from .models import Service
    return {
        "footer_services": Service.objects.all().order_by("order")
    }
def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug)
    return render(request, "website/service_detail.html", {"service":service})


@login_required(login_url='admin_login')
def edit_service(request, pk):
    service = get_object_or_404(Service, pk=pk)

    if request.method == "POST":
        service.title = request.POST.get('title')
        service.description = request.POST.get('description')
        service.full_description = request.POST.get('full_description')
        service.icon = request.POST.get('icon')
        service.color = request.POST.get('color')
        service.order = request.POST.get('order') or 0

        # Slug logic
        slug_input = request.POST.get('slug')
        if slug_input and slug_input.strip().lower() != 'none':
            service.slug = slug_input
        elif not service.slug or service.slug == 'None':
            service.slug = slugify(service.title)

        # Remove Image (if remove flag = 1)
        if request.POST.get("remove_image") == "1":
            if service.image:
                service.image.delete(save=False)
            service.image = None

        # Upload new image — this always runs AFTER remove image check
        elif 'image' in request.FILES:
            service.image = request.FILES['image']

        service.save()
        messages.success(request, "Service updated successfully!")
        return redirect('manage_services')

    return render(request, 'website/edit_service.html', {'service': service})


#  DELETE SERVICE 
@login_required(login_url='admin_login')
def delete_service(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        title = service.title
        service.delete()
        messages.error(request, f'"{title}" has been deleted successfully.')
        return redirect('manage_services')
    return render(request, 'website/delete_service.html', {'service': service})


#  MANAGE BLOG POSTS 
@login_required(login_url='admin_login')
def manage_blog_posts(request):
    posts = BlogPost.objects.all().order_by('-created_at')

    if request.method == 'POST':
        title = request.POST.get('title')
        summary = request.POST.get('summary')
        content = request.POST.get('content')
        status = request.POST.get('status', 'draft')
        image = request.FILES.get('featured_image')
        slug_value = slugify(title)
        published_date = timezone.now() if status == 'published' else None

       
        if BlogPost.objects.filter(slug=slug_value).exists():
            messages.error(request, f'A blog post with the title "{title}" already exists. Please use a different title.')
            return redirect('manage_blog_posts')

        BlogPost.objects.create(
            title=title,
            slug=slug_value,
            author=request.user,
            summary=summary,
            content=content,
            featured_image=image,
            status=status,
            published_date=published_date,
        )
        messages.success(request, f'New blog post "{title}" added successfully!')
        return redirect('manage_blog_posts')

    return render(request, 'website/manage_blog_posts.html', {'posts': posts})



# Edit blog
@login_required(login_url='admin_login')
def edit_blog_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == "POST":
        post.title = request.POST.get('title')
        post.summary = request.POST.get('summary')
        post.content = request.POST.get('content')
        post.status = request.POST.get('status', 'draft')
        slug_input = request.POST.get('slug')

        if slug_input and slug_input.strip().lower() != 'none':
            post.slug = slug_input
        elif not post.slug or post.slug == 'None':
            post.slug = slugify(post.title)

        if 'featured_image' in request.FILES:
            post.featured_image = request.FILES['featured_image']

        if post.status == 'published' and not post.published_date:
            post.published_date = timezone.now()

        post.save()
        messages.success(request, f'Blog post "{post.title}" updated successfully!')
        return redirect('manage_blog_posts')

    return render(request, 'website/edit_blog_post.html', {'post': post})


@login_required(login_url='admin_login')
def delete_blog_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == "POST":
        title = post.title
        post.delete()
        messages.error(request, f'Blog post "{title}" deleted successfully.')
        return redirect('manage_blog_posts')
    return render(request, 'website/delete_blog_post_confirm.html', {'post': post})


#  PUBLIC BLOG VIEWS 
def blog_list(request):
    posts = BlogPost.objects.filter(status='published').order_by('-published_date')
    return render(request, 'website/blog_list.html', {'posts': posts})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    return render(request, 'website/blog_detail.html', {'post': post})


#  MANAGE JOBS 
@login_required(login_url='admin_login')
def manage_jobs(request):
    jobs = Job.objects.all().order_by('-posted_at')

    if request.method == 'POST':
        title = request.POST.get('title')
        location = request.POST.get('location')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        is_active = request.POST.get('is_active') == 'on'

        Job.objects.create(
            title=title,
            location=location,
            description=description,
            requirements=requirements,
            is_active=is_active
        )
        messages.success(request, 'New job added successfully!')
        return redirect('manage_jobs')

    return render(request, 'website/manage_jobs.html', {'jobs': jobs})


#  MANAGE APPLICATIONS 
@login_required(login_url='admin_login')
def manage_applications(request):
    """
    Purpose:
    Admin view to manage and review all candidate job applications.
    Provides filtering options by job title and date range, 
    and allows status updates directly from the admin dashboard.

    Features:
    - Filter by Job
    - Filter by Application Date Range
    - Inline Status Updates (Received, Shortlisted, Rejected, Withdrawn)
    - Displays candidate info and documents

    Template: website/manage_applications.html
    """

    applications = (
        JobApplication.objects.select_related('job', 'candidate')
        .order_by('-applied_at')
    )
    jobs = Job.objects.all()

    job_filter = request.GET.get('job')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if job_filter:
        applications = applications.filter(job__id=job_filter)
    if start_date and end_date:
        applications = applications.filter(applied_at__range=[start_date, end_date])

    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        new_status = request.POST.get('status')

        if app_id and new_status:
            application = get_object_or_404(JobApplication, id=app_id)
            previous_status = application.status
            application.status = new_status
            application.save()

            messages.success(
                request,
                f"Application for {application.full_name} "
                f"({application.job.title}) updated from {previous_status.title()} "
                f"to {new_status.title()}."
            )
            return redirect('manage_applications')

    
    context = {
        'applications': applications,
        'jobs': jobs,
        'selected_job': job_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'website/manage_applications.html', context)


#  SERVICE DETAIL 
def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug)
    return render(request, 'website/service_detail.html', {'service': service})


#  EDIT SERVICE 



#  SCHEDULE DEMO
logger = logging.getLogger(__name__)


def schedule_demo(request):
    """
    AJAX-enabled Schedule Demo view.

    Behavior:
    - GET: render the schedule demo page (normal flow).
    - POST (AJAX): returns JSON responses (success / validation errors / server errors).
    - POST (normal form submit): redirect or render a success message (for non-AJAX clients).
    - Prevents duplicate booking for the same company + email within 24 hours.
    """

    company_name = request.POST.get('company') or request.GET.get('service') or 'Propulsion Service'

    # Detect AJAX (fetch sets X-Requested-With: XMLHttpRequest)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # GET → normal page render
    if request.method != "POST":
        form = ScheduleDemoForm(initial={'company': company_name})
        return render(request, "website/schedule_demo.html", {"form": form})

    # POST → handle submission
    form = ScheduleDemoForm(request.POST)

    # If form invalid -> respond appropriately
    if not form.is_valid():
        try:
            errors = form.errors.get_json_data()
        except Exception:
            errors = {k: form.errors.get(k) for k in form.errors}

        if is_ajax:
            return JsonResponse({
                "success": False,
                "error": "Please correct the form errors.",
                "form_errors": errors
            }, status=400)
        else:
            return render(request, "website/schedule_demo.html", {"form": form})

    try:
        email = form.cleaned_data.get("email")
        phone = form.cleaned_data.get("phone")
        company = form.cleaned_data.get("company") or company_name

        # 24-hour duplicate booking window (company + email)
        cutoff = timezone.now() - timedelta(hours=24)
        existing = ScheduleDemo.objects.filter(
            email__iexact=email,
            company__iexact=company,
            created_at__gte=cutoff
        ).exists()

        if existing:
            msg = (
                f"You’ve already scheduled a demo for '{company}' in the last 24 hours. "
                "You can still schedule demos for other services."
            )

            if is_ajax:
                return JsonResponse({"success": False, "error": msg}, status=400)
            else:
                messages.error(request, msg)
                return redirect(request.META.get('HTTP_REFERER', reverse('home')))

        # -------------------------------  
        # ✅ FIX: Correctly parse scheduled_date from datetime-local input
        # -------------------------------
        raw_date = request.POST.get("scheduled_date")   # e.g., "2025-11-18T15:30"

        parsed_dt = parse_datetime(raw_date)            # Convert string → Python datetime

        if parsed_dt is not None:
            parsed_dt = timezone.make_aware(parsed_dt)  # Apply timezone
        else:
            parsed_dt = None

        # Save the demo using manual date instead of broken default
        with transaction.atomic():
            demo = form.save(commit=False)
            demo.company = company
            demo.scheduled_date = parsed_dt   # <-- FIX APPLIED HERE
            demo.save()

        # Prepare details for email
        user_name = demo.name
        recipient_email = demo.email

        details = {
            'Name': user_name,
            'Email': recipient_email,
            'Phone': demo.phone,
            'Company/Service': demo.company,
            'Preferred Date & Time': demo.scheduled_date.strftime("%Y-%m-%d %H:%M") if demo.scheduled_date else 'N/A',
            'Message Snippet': (demo.message[:50] + '...') if demo.message else 'N/A'
        }

        try:
            cta_url = settings.DEFAULT_SITE_URL.rstrip("/") + reverse("schedule_demo")
        except Exception:
            cta_url = request.build_absolute_uri(reverse("schedule_demo"))

        try:
            send_confirmation_email(
                recipient_email,
                user_name,
                "Schedule Demo",
                details,
                cta_url=cta_url
            )
        except Exception as email_err:
            logger.exception("Failed to send confirmation email for Schedule Demo (id=%s): %s",
                             getattr(demo, 'id', 'n/a'), email_err)

        if is_ajax:
            return JsonResponse({
                "success": True,
                "message": "Your demo has been scheduled successfully!",
                "demo_id": getattr(demo, "id", None)
            })
        else:
            messages.success(request, "Your demo has been scheduled successfully! We will contact you shortly.")
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    except Exception as e:
        logger.exception("Error during schedule_demo submission: %s", e)

        if is_ajax:
            return JsonResponse({
                "success": False,
                "error": "Unexpected system error. Please try again later."
            }, status=500)
        else:
            messages.error(request, "Unexpected system error. Please try again later.")
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))

#  MANAGE DEMO REQUESTS 
@login_required(login_url='admin_login')
def manage_demo_requests(request):
    demo_requests = ScheduleDemo.objects.all().order_by("-created_at", "-id")
    experts = Expert.objects.all().order_by("full_name")

    # ---------------- POST REQUEST -----------------
    if request.method == "POST":
        demo_id = request.POST.get("id") or request.POST.get("demo_id")
        expert_id = request.POST.get("expert_id")
        action = request.POST.get("action")

        if not demo_id:
            messages.error(request, "Invalid request: missing demo ID.")
            return redirect("manage_demo_requests")

        try:
            demo = ScheduleDemo.objects.get(id=demo_id)
        except ScheduleDemo.DoesNotExist:
            messages.error(request, "Demo request not found.")
            return redirect("manage_demo_requests")

        # -------- ASSIGN --------
        if action == "assign":
            if demo.scheduled_date and demo.scheduled_date < timezone.now():
                messages.error(request, "You cannot assign this request because the scheduled date is already in the past.")
                return redirect("manage_demo_requests")

            if not expert_id:
                messages.error(request, "Please select an expert before assigning.")
                return redirect("manage_demo_requests")

            try:
                expert = Expert.objects.get(id=expert_id)
                demo.assigned_expert = expert
                demo.status = "assigned"
                demo.save()

                messages.success(
                    request,
                    f"Assigned demo '{demo.company or demo.name}' to {expert.full_name or expert.username}."
                )

            except Expert.DoesNotExist:
                messages.error(request, "Selected expert does not exist.")
                return redirect("manage_demo_requests")

        # -------- DECLINE --------
        elif action == "decline":
            decline_reason = request.POST.get("decline_reason", "No reason provided.")
            demo.assigned_expert = None
            demo.status = "declined"
            demo.save()

            try:
                send_confirmation_email(
                    demo.email,
                    demo.name,
                    "Demo Request Declined",
                    {"Reason": decline_reason},
                    template_name="website/decline_email.html"
                )
            except Exception:
                logger.exception("Failed to send decline email.")

            messages.error(request, f"Demo request from {demo.name} declined.")
        
        else:
            messages.error(request, "Unknown action.")

        return redirect("manage_demo_requests")

    # ---------------- GET REQUEST (IMPORTANT PART!) -----------------
    return render(
        request,
        "website/manage_demo_requests.html",
        {
            "demo_requests": demo_requests,
            "experts": experts,
        }
    )





def careers_list(request):
    """
    View to display job listings with filtering capabilities.
    """
    # Start with all active jobs, sorted by newest
    jobs = Job.objects.filter(is_active=True).order_by('-posted_at')

    # --- 1. Filter by Position ---
    position_query = request.GET.get('position')
    if position_query:
        jobs = jobs.filter(title__icontains=position_query)

    # --- 2. Filter by Skills ---
    # This searches the job title, summary, and description for the keyword.
    # If you have a specific tags field, add it to the Q object below.
    skills_query = request.GET.get('skills')
    if skills_query:
        jobs = jobs.filter(
            Q(title__icontains=skills_query) |
            Q(description__icontains=skills_query) |
            Q(requirements__icontains=skills_query)
        ).distinct()

    # --- 3. Filter by Date Posted ---
    date_query = request.GET.get('date_posted')
    if date_query:
        now = timezone.now()
        if date_query == 'today':
            start_date = now - timedelta(days=1)
            jobs = jobs.filter(posted_at__gte=start_date)
        elif date_query == 'week':
            start_date = now - timedelta(weeks=1)
            jobs = jobs.filter(posted_at__gte=start_date)
        elif date_query == 'month':
            start_date = now - timedelta(days=30)
            jobs = jobs.filter(posted_at__gte=start_date)

    context = {
        'jobs': jobs,
    }
    
    return render(request, 'website/careers_list.html', context)




# APPLY JOB
logger = logging.getLogger(__name__)

@login_required(login_url='candidate_login')
def apply_job(request, pk):
    """
    Handles job applications:
    - Auto-fills name, email, phone from CandidateProfile
    - Prevents duplicate submissions
    - Sends confirmation email safely
    - Redirects to confirmation page after success
    """
    job = get_object_or_404(Job, pk=pk)
    user = request.user

    # --- Prevent duplicate applications ---
    if JobApplication.objects.filter(job=job, candidate=user).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('careers_list')

    # --- Load candidate profile with phone, legal names ---
    try:
        profile = CandidateProfile.objects.get(user=user)
        middle_name = profile.middle_name or ""
        full_name = f"{profile.first_name_legal} {middle_name} {profile.last_name}".strip()
        phone = profile.phone_number or ""
    except CandidateProfile.DoesNotExist:
        full_name = user.get_full_name() or user.username
        phone = ""

    # -----------------------------
    # POST → Save Application
    # -----------------------------
    if request.method == 'POST':
        
        form = JobApplicationForm(request.POST, request.FILES)
      

        if form.is_valid():
            try:
                with transaction.atomic():

                    application = form.save(commit=False)
                    application.job = job
                    application.candidate = user

                    # Auto-fill fields
                    print("@@@@",form.cleaned_data.get("experience_years"))
                    application.full_name = form.cleaned_data.get('full_name') or full_name
                    application.email = form.cleaned_data.get('email') or user.email
                    application.phone = form.cleaned_data.get('phone') or phone
                    application.experience_years = form.cleaned_data.get('experience_years') 
                    # -------------------------------
                    # FIXED: Experience Save Logic
                    # -------------------------------
                    exp = form.cleaned_data.get("experience_years")
                    print("@@@@@@@@@@@@@@@@@@@@@@@@",exp)


                    # Save application
                    application.save()

                # -----------------------------
                # Prepare confirmation email
                # -----------------------------
                user_name = application.full_name
                recipient_email = application.email
                ist_time = application.applied_at.astimezone(timezone.get_fixed_timezone(330))

                details = {
                    'Job Title': job.title,
                    'Application Status': application.get_status_display(),
                    'Applied On': ist_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'Phone': application.phone or 'N/A',
                    'Cover Letter Snippet': (application.cover_letter[:50] + '...') if application.cover_letter else 'N/A',
}

                try:
                    dashboard_path = reverse('candidate_dashboard')
                    cta_url = request.build_absolute_uri(dashboard_path)
                except:
                    cta_url = request.build_absolute_uri('/candidate/dashboard/')

                # Send Email
                try:
                    send_confirmation_email(
                        recipient_email,
                        user_name,
                        "Job Application Submitted",
                        details,
                        template_name='website/confirmation_email.html',
                        cta_url=cta_url
                    )
                except Exception as e:
                    logger.exception(
                        "Failed to send application confirmation email for application id=%s: %s",
                        getattr(application, 'id', 'n/a'),
                        e
                    )

                messages.success(request, "Your application has been submitted successfully!")

                # Redirect to confirmation
                return redirect('application_confirmation', application_id=application.id)

            except Exception as e:
                logger.exception(
                    "Error saving job application for user %s job %s: %s",
                    user.id,
                    job.id,
                    e
                )
                messages.error(request, "An unexpected error occurred. Please try again.")

        else:
            messages.error(request, "Please correct the errors and try again.")

    # -----------------------------
    # GET → Prefill Form
    # -----------------------------
    else:
        form = JobApplicationForm(initial={
            'full_name': full_name,
            'email': user.email,
            'phone': phone,
        })

    return render(request, 'website/apply_job.html', {
        'form': form,
        'job': job
    })


# Confirmation Page View

def application_confirmation(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    return render(request, 'website/application_confirmation.html', {
        'application': application
    })

#  CANDIDATE REGISTER
def candidate_register(request):
    if request.method == 'POST':
        form = CandidateRegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['preferred_email']
            
          
            existing_user = User.objects.filter(email__iexact=email).first()
            
            if not existing_user:
                existing_user = User.objects.filter(username=username).first()
            
            if existing_user:
                if not existing_user.is_active:
                    try:
                        profile = CandidateProfile.objects.get(user=existing_user)
                        profile.delete()
                    except CandidateProfile.DoesNotExist:
                        pass
                  
                    existing_user.delete() 
                    messages.info(request, "Previous unverified registration found. Please complete registration again.")
                else:
                    messages.error(request, "A verified account already exists with this username or email. Please use a different email or log in to your existing account.")
                    return render(request, 'website/candidate_register.html', {'form': form})
            
            user = User.objects.create_user(
                username=username,
                password=form.cleaned_data['password'],
                email=email,
                first_name=form.cleaned_data['first_name_legal'],
                last_name=form.cleaned_data['last_name'],
                is_active=False
            )
            
            candidate_profile = CandidateProfile.objects.create(
                user=user,
                first_name_legal=form.cleaned_data['first_name_legal'],
                middle_name=form.cleaned_data.get('middle_name'),
                last_name=form.cleaned_data['last_name'],
                phone_number=form.cleaned_data['phone_number'],
                address_line1=form.cleaned_data['address_line1'],
                country=form.cleaned_data['country'],
                state=form.cleaned_data['state'],
                city=form.cleaned_data['city'],
                school=form.cleaned_data['school']
            )

            user_name = f"{user.first_name} {user.last_name}"
            if generate_and_send_otp(candidate_profile, email, user_name, "Candidate"):
                request.session['candidate_user_id'] = user.id
                messages.info(request, f" A verification code has been sent to {email}.")
                return redirect('candidate_otp_verify')
            else:
             
                user.delete()
                messages.error(request, "Failed to send verification email. Please try again.")
                return redirect('candidate_register')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CandidateRegisterForm()

    return render(request, 'website/candidate_register.html', {'form': form})


#  CANDIDATE LOGIN
from .utils import generate_and_send_otp  

def candidate_login(request):
    """
    Candidate login view — handles messages and redirects back to
    the intended page (e.g., job application form) after successful login.
    """
    next_url = request.GET.get('next', '')  

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        next_url = request.POST.get('next', '') or next_url  

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'website/candidate_login.html', {'next': next_url})

        user = authenticate(request, username=username, password=password)

        if user:
            if user.is_staff:
                messages.error(request, "Admin accounts cannot log in from the candidate portal.")
                return redirect('candidate_login')

            if user.is_active:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                return redirect(next_url or 'home')

            else:
                try:
                    profile = CandidateProfile.objects.get(user=user)
                    if generate_and_send_otp(profile, user.email, user.get_full_name() or user.username, "Candidate"):
                        request.session['candidate_user_id'] = user.id
                        messages.warning(request, f"Account not verified. OTP resent to {user.email}.")
                    else:
                        messages.error(request, "Account not verified and failed to send OTP. Please contact support.")
                except CandidateProfile.DoesNotExist:
                    messages.error(request, "Account not verified. Please register again.")

                return redirect('candidate_otp_verify')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, 'website/candidate_login.html', {'next': next_url})

    return render(request, 'website/candidate_login.html', {'next': next_url})

#  CANDIDATE LOGOUT 
@login_required(login_url='candidate_login')
def candidate_logout(request):
    logout(request)
    return redirect('candidate_logged_out')


def candidate_logged_out_view(request):
    """
    Displays a confirmation page after successful logout.
    """
    return render(request, 'website/candidate_logged_out.html', {
        'message': "You have been logged out successfully."
    })


#  CANDIDATE DASHBOARD 
@login_required(login_url='candidate_login')
def candidate_dashboard(request):
    """
    Candidate dashboard displaying all submitted job applications.
    Candidates can also withdraw (delete) their applications.
    """
    applications = JobApplication.objects.filter(candidate=request.user).order_by('-applied_at')

    if request.method == "POST":
        app_id = request.POST.get("application_id")
        if app_id:
            try:
                application = JobApplication.objects.get(id=app_id, candidate=request.user)
                application.delete()  
                messages.success(request, " Your application has been withdrawn successfully.")
                return redirect('candidate_dashboard')
            except JobApplication.DoesNotExist:
                messages.error(request, " Application not found or already withdrawn.")
                return redirect('candidate_dashboard')

    for app in applications:
        if app.status == "received":
            app.display_status = "Submitted"
        elif app.status == "shortlisted":
            app.display_status = "Shortlisted"
        elif app.status == "rejected":
            app.display_status = "Rejected"
        elif app.status == "withdrawn":
            app.display_status = "Withdrawn"
        else:
            app.display_status = "Pending"

    return render(request, 'website/candidate_dashboard.html', {
        'applications': applications
    })

#  EDIT JOB 
@login_required(login_url='admin_login')
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.location = request.POST.get('location')
        job.description = request.POST.get('description')
        job.requirements = request.POST.get('requirements')
        job.is_active = request.POST.get('is_active') == 'on'
        job.save()
        messages.success(request, "Job updated successfully!")
        return redirect('manage_jobs')
    return render(request, 'website/edit_job.html', {'job': job})

# DELETE JOB
@login_required(login_url='admin_login')
def delete_job(request, pk):
    if request.method == "POST":
        try:
            job = get_object_or_404(Job, pk=pk)
            job.delete()
            messages.error(request, "Job deleted successfully!")  # RED
            return redirect('manage_jobs')
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('manage_jobs')

    messages.error(request, "Invalid request.")
    return redirect('manage_jobs')
                  
#  ASK EXPERT 
def ask_expert(request):
    if request.method == "POST":
        service_slug = request.POST.get('service_slug')
        
        try:
            redirect_url = reverse('service_detail', kwargs={'slug': service_slug})
        except:
            redirect_url = reverse('home')
        
        service = get_object_or_404(Service, slug=service_slug)
        form = ExpertQueryForm(request.POST)

        if form.is_valid():
            expert_query = None 
            
            try:
                with transaction.atomic():
                    expert_query = form.save(commit=False)
                    expert_query.service = service
                    expert_query.save()

                user_name = expert_query.name
                recipient_email = expert_query.email
                details = {
                    'Job Title': expert_query.service.title,
                    'Application Status': "Submitted",
                    'Applied On': expert_query.submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
                    'Phone': expert_query.phone or 'N/A',
                    'Cover Letter Snippet': expert_query.message[:50] + '...',
                }
                cta_url = settings.DEFAULT_SITE_URL + redirect_url 
                
                email_sent = send_confirmation_email(recipient_email, user_name, "Expert Query", details, cta_url=cta_url)

                if email_sent:
                    messages.success(request, " Your query has been submitted successfully! Our expert will contact you soon.")
                else:
                    messages.warning(request, " Your query was submitted, but we failed to send the confirmation email.")

                return redirect(redirect_url) 
            
            except Exception as e:
                print(f"Error during ask_expert submission: {e}")
                
                if 'IntegrityError' in str(e):
                    messages.error(request, " An error occurred during submission (database ID conflict). Please contact support.")
                else:
                    messages.error(request, " An unexpected error occurred during submission. Please check your inputs and try again.")

                return redirect(redirect_url)

        else:
            messages.error(request, " There was an error with your query submission. Please check your inputs.")
            return redirect(redirect_url)


    return redirect('home')


#  MANAGE EXPERT QUERIES
@login_required(login_url='admin_login')
def manage_expert_queries(request):
    queries = ExpertQuery.objects.filter(
        Q(status='pending') | Q(status='accepted') | Q(status='rejected')
    ).select_related('service').order_by('-submitted_at')

    experts = Expert.objects.all().order_by('full_name')

    # -------------------------
    # POST REQUEST HANDLING
    # -------------------------
    if request.method == "POST":

        query_id = request.POST.get('id') or request.POST.get('query_id')
        expert_id = request.POST.get('expert_id')
        action = request.POST.get('action')

        # Validate action
        if not action:
            messages.error(request, "Invalid action.")
            return redirect('manage_expert_queries')

        # Validate query ID
        if not query_id:
            messages.error(request, "Missing query ID.")
            return redirect('manage_expert_queries')

        # Fetch query object
        try:
            query = ExpertQuery.objects.get(id=query_id)
        except ExpertQuery.DoesNotExist:
            messages.error(request, "Expert query not found.")
            return redirect('manage_expert_queries')

        # -------------------------
        # ASSIGN QUERY
        # -------------------------
        if action == "assign":

            if not expert_id:
                messages.error(request, "No expert selected.")
                return redirect('manage_expert_queries')

            try:
                expert = Expert.objects.get(id=expert_id)
            except Expert.DoesNotExist:
                messages.error(request, "Selected expert does not exist.")
                return redirect('manage_expert_queries')

            try:
                with transaction.atomic():
                    query.assigned_expert = expert
                    query.status = "assigned"
                    query.save()

                expert_display = (expert.full_name or expert.username)
                messages.success(request, f"Assigned query from '{query.name}' to {expert_display}.")

            except Exception as e:
                logger.exception("Error assigning expert for query id %s: %s", query_id, e)
                messages.error(request, "An error occurred while assigning the expert.")
                return redirect('manage_expert_queries')

        # -------------------------
        # DECLINE QUERY
        # -------------------------
        elif action == "decline":

            decline_reason = request.POST.get(
                'decline_reason',
                'The query did not fit our expert capacity or scope.'
            )

            try:
                with transaction.atomic():
                    query.assigned_expert = None
                    query.status = "declined"
                    query.decline_reason = decline_reason
                    query.save()

                # Prepare email content
                user_name = query.name
                recipient_email = query.email
                intro_message = (
                    f"We have reviewed your request and regret to inform you that your Expert Query "
                    f"related to the '{query.service.title}' service has been declined."
                )

                details = {
                    'Status': 'Declined',
                    'Reason Provided': decline_reason,
                    'Service Requested': query.service.title,
                    'Original Message Snippet': query.message[:50] + '...',
                    'Submitted On': query.submitted_at.strftime("%Y-%m-%d %H:%M:%S")
                }

                # Send decline email
                try:
                    send_confirmation_email(
                        recipient_email,
                        user_name,
                        "Expert Query (Declined)",
                        details,
                        template_name='website/decline_email.html',
                        extra_context={'intro_message': intro_message}
                    )
                except Exception as e:
                    logger.exception(
                        "Failed to send decline email for query id %s: %s",
                        query.id, e
                    )

                messages.warning(
                    request,
                    f"Query from {query.name} declined and client notified."
                )

            except Exception as e:
                logger.exception("Error declining query id %s: %s", query.id, e)
                messages.error(request, "An error occurred while declining the query.")
                return redirect('manage_expert_queries')

        return redirect('manage_expert_queries')

    # -------------------------
    # GET REQUEST
    # -------------------------
    return render(request, 'website/manage_expert_queries.html', {
        'queries': queries,
        'experts': experts,
    })

#  MANAGE ASSIGNED QUERIES 
@login_required(login_url='admin_login')
def manage_assigned_queries(request):
    queries = ExpertQuery.objects.filter(status='assigned')
    queries = filter_queries(request, queries)
    
    return render(request, 'website/manage_assigned_queries.html', {
        'queries': queries,
        'current_filter': request.GET.get('date_filter', ''),
        'current_sort': request.GET.get('sort_by', 'latest'),
    })


#  MANAGE DECLINED QUERIES 
@login_required(login_url='admin_login')
def manage_declined_queries(request):
    queries = ExpertQuery.objects.filter(status='declined')
    queries = filter_queries(request, queries)

    if request.method == "POST" and request.POST.get('action') == 'delete':
        query_id = request.POST.get('query_id')
        try:
            query = get_object_or_404(ExpertQuery, id=query_id, status='declined')
            query.delete()
            messages.error(request, f" Declined query from {query.name} successfully deleted.")
        except Exception:
            messages.error(request, " Could not delete the declined query.")
        
        return redirect(request.path + '?' + request.META.get('QUERY_STRING', ''))
    
    return render(request, 'website/manage_declined_queries.html', {
        'queries': queries,
        'current_filter': request.GET.get('date_filter', ''),
        'current_sort': request.GET.get('sort_by', 'latest'),
    })


@login_required(login_url='admin_login')
def manage_client_responses(request):
    messages_data = ContactMessage.objects.all().order_by('-submitted_at')

    from_date = request.GET.get('from')
    to_date = request.GET.get('to')
    download = request.GET.get('download')

    # --- Apply Date Filters ---
    if from_date:
        try:
            messages_data = messages_data.filter(submitted_at__date__gte=from_date)
        except:
            pass

    if to_date:
        try:
            messages_data = messages_data.filter(submitted_at__date__lte=to_date)
        except:
            pass

    # --- Handle Excel Download ---
    if download == "excel":
        return export_client_responses_to_excel(messages_data)

    return render(request, 'website/manage_client_responses.html', {
        'messages_data': messages_data,
        'request': request,   # Needed for template download link
    })


def export_client_responses_to_excel(queryset):
    import openpyxl
    from django.http import HttpResponse

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Client Responses"

    # Excel Header Row
    ws.append(["Name", "Email", "Subject", "Message", "Submitted At", "Attachment"])

    for msg in queryset:
        ws.append([
            msg.name,
            msg.email,
            msg.subject,
            msg.message,
            msg.submitted_at.strftime('%Y-%m-%d %H:%M'),
            msg.attachment.url if msg.attachment else "No File"
        ])

    # Prepare File Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="client_responses.xlsx"'

    wb.save(response)
    return response



#  EXPERT REGISTER 
logger = logging.getLogger(__name__)

def expert_register_view(request):
    logger.info("expert_register_view called; method=%s, POST keys=%s", request.method, list(request.POST.keys()))

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip().lower()
        password = (request.POST.get("password") or "").strip()
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()

        logger.info("Register attempt: username=%s email=%s", username, email)

        if not username or not password or not email:
            messages.error(request, "Username, password, and email are required.")
            logger.warning("Missing required fields.")
            return render(request, "website/expert_register.html")

        try:
              existing_expert = Expert.objects.filter(
             Q(email__iexact=email) | Q(username__iexact=username)
               ).first()   
        except Exception as e:
            logger.exception("DB error when checking existing expert")
            messages.error(request, "Internal server error. Try again later.")
            return render(request, "website/expert_register.html")

        if existing_expert:
            logger.info(
                "Found existing_expert id=%s status=%s otp_code_present=%s",
                existing_expert.id,
                getattr(existing_expert, "status", None),
                bool(getattr(existing_expert, "otp_code", None))
            )

            if getattr(existing_expert, "status", None) == "unverified":
                try:
                    sent = generate_and_send_otp(
                        existing_expert,
                        decrypt_data(existing_expert.email),
                        existing_expert.full_name or existing_expert.username,
                        "Expert"
                    )
                except Exception:
                    logger.exception("generate_and_send_otp raised an exception for existing expert")
                    sent = False

                if sent:
                    request.session["expert_id_unverified"] = existing_expert.id
                    messages.warning(
                        request,
                        f"Previous registration incomplete — OTP resent to {decrypt_data(existing_expert.email)}."
                    )
                    logger.info("Redirecting to expert_otp_verify (resend successful).")
                    return redirect("expert_otp_verify")
                else:
                    messages.error(request, "Failed to resend OTP. Contact support or try again.")
                    return redirect("expert_register")

            elif getattr(existing_expert, "status", None) == "pending":
                messages.info(request, "Your account is verified but pending admin approval.")
                logger.info("Existing expert pending admin; redirecting to login.")
                return redirect("expert_login")

            elif getattr(existing_expert, "status", None) == "approved":
                messages.error(request, "An approved account already exists. Please log in.")
                logger.info("Existing expert approved; redirecting to login.")
                return redirect("expert_login")

            elif getattr(existing_expert, "status", None) == "rejected":
                messages.error(request, "Your previous registration was rejected. Contact support.")
                logger.info("Existing expert rejected; redirecting to login.")
                return redirect("expert_login")

        try:
            hashed_pw = make_password(password)
            expert = Expert.objects.create(
                username=username,
                password=hashed_pw,
                full_name=full_name,
                email=email,
                status="unverified",   
            )
            logger.info("Created new Expert id=%s (status=unverified)", expert.id)
        except Exception:
            logger.exception("Failed to create Expert")
            messages.error(request, "Failed to create account. Try again.")
            return render(request, "website/expert_register.html")

        try:
            sent = generate_and_send_otp(
                expert,
                decrypt_data(expert.email),
                full_name or username,
                "Expert"
            )
        except Exception:
            logger.exception("generate_and_send_otp raised an exception for new expert")
            sent = False

        logger.info("generate_and_send_otp returned %s for new Expert id=%s", sent, expert.id)

        if sent:
            request.session["expert_id_unverified"] = expert.id
            messages.success(
                request,
                f" A verification code has been sent to {decrypt_data(expert.email)}."
            )
            logger.info("Redirecting to expert_otp_verify after successful send.")
            return redirect("expert_otp_verify")
        else:
            logger.error("Failed to send OTP after creating expert; deleting created expert.")
            expert.delete()
            messages.error(request, "Failed to send verification email. Please try again.")
            return render(request, "website/expert_register.html")

    return render(request, "website/expert_register.html")


def expert_login_view(request):
    """
    Handles expert login with OTP verification and admin approval check.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if len(username) > 50:
            messages.error(request, 'Username must be 50 characters or less.')
            return redirect('expert_login')
        
        if len(password) > 100:
               messages.error(request, 'Password is too long.')
               return redirect('expert_login')

        try:
            expert = Expert.objects.get(username=username)

            if expert.status == 'pending':
                messages.warning(request, "Your registration is pending admin approval. Please wait for approval before logging in.")
                return redirect('expert_login')
            elif expert.status == 'rejected':
                messages.error(request, "Your registration request was rejected by admin. Contact support for details.")
                return redirect('expert_login')

            if expert.otp_code:
                if generate_and_send_otp(expert, expert.email, expert.full_name or expert.username, "Expert"):
                    request.session['expert_id_unverified'] = expert.id
                    messages.warning(request, f"Your account is unverified. We have resent the OTP to {expert.email}.")
                    return redirect('expert_otp_verify')
                else:
                    messages.error(request, "Verification required, but failed to resend OTP. Please try again later.")
                    return redirect('expert_login')

            if check_password(password, expert.password):
                request.session['expert_id'] = expert.id
                request.session['expert_name'] = expert.full_name or expert.username
                request.session.set_expiry(3600)  
                messages.success(request, f"Welcome back, {expert.full_name or expert.username}!")
                return redirect('expert_dashboard')
            else:
                messages.error(request, 'Invalid password.')

        except Expert.DoesNotExist:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'website/expert_login.html')

def expert_dashboard_view(request):
    expert_id = request.session.get("expert_id")
    if not expert_id:
        messages.error(request, "Please log in to continue.")
        return redirect("expert_login")

    expert = Expert.objects.get(id=expert_id)

    expert_name = expert.full_name or expert.username
    expert_email = expert.email
    expert_initial = expert_name[0].upper() if expert_name else "E"

    assigned_queries_count = ExpertQuery.objects.filter(
        assigned_expert=expert
    ).count()

    assigned_demos_count = ScheduleDemo.objects.filter(
        assigned_expert=expert
    ).count()

    completed_tasks = (
        ExpertQuery.objects.filter(assigned_expert=expert, status="completed").count() +
        ScheduleDemo.objects.filter(assigned_expert=expert, status="completed").count()
    )

    return render(request, "website/expert_dashboard.html", {
        "expert_name": expert_name,
        "expert_email": expert_email,
        "expert_initial": expert_initial,
        "assigned_queries_count": assigned_queries_count,
        "assigned_demos_count": assigned_demos_count,
        "completed_tasks": completed_tasks,
    })




def expert_logout_view(request):
    """
    Logs out the expert and redirects directly to the homepage.
    """
    request.session.flush()  
    return redirect('home')  



def expert_assigned_queries_view(request):

    # Check if expert is logged in using session-based authentication
    expert_id = request.session.get("expert_id")
    if not expert_id:
        messages.error(request, "Please log in to continue.")
        return redirect("expert_login")

    expert = Expert.objects.get(id=expert_id)

    # Fetch assigned queries
    assigned_queries = ExpertQuery.objects.filter(
        assigned_expert=expert
    ).order_by('-submitted_at')

    # Handle POST actions
    if request.method == "POST":
        action = request.POST.get("action")
        query_id = request.POST.get("query_id")
        query = get_object_or_404(ExpertQuery, id=query_id)

        # ===== ACCEPT QUERY =====
        if action == "accept":
            query.status = "accepted"
            query.save()

            # Email details
            details = {
                "Service": query.service.title,
                "Message Snippet": query.message[:50] + "..."
            }

            # SEND ACCEPTANCE EMAIL
            send_expert_accept_email(
                query.email,
                query.name,
                expert.full_name or expert.username,
                "Expert Query",
                details
            )

            messages.success(request, "Query accepted and email sent to customer.")
            return redirect("expert_assigned_queries")

        # ===== REJECT QUERY =====
        elif action == "reject":
            reason = request.POST.get("reject_reason", "").strip()

            query.status = "rejected"
            query.expert_reject_reason = reason
            query.save()

            details = {
                "Service": query.service.title,
                "Message Snippet": query.message[:50] + "...",
                "Reason": reason,
            }

            # SEND REJECTION EMAIL
            send_expert_rejection_email(
                query.email,
                query.name,
                expert.full_name or expert.username,
                "Expert Query",
                details
            )

            messages.error(request, "Query rejected and email sent to customer.")
            return redirect("expert_assigned_queries")

    return render(request, "website/expert_assigned_queries.html", {
        "assigned_queries": assigned_queries
    })


def expert_assigned_demos_view(request):

    # Check session-based login
    expert_id = request.session.get("expert_id")
    if not expert_id:
        messages.error(request, "Please log in to continue.")
        return redirect("expert_login")

    expert = Expert.objects.get(id=expert_id)

    # Fetch assigned demos
    assigned_demos = ScheduleDemo.objects.filter(
        assigned_expert=expert
    ).order_by('-created_at')

    # Handle POST
    if request.method == "POST":
        action = request.POST.get("action")
        demo_id = request.POST.get("demo_id")
        demo = get_object_or_404(ScheduleDemo, id=demo_id)

        # ===== ACCEPT DEMO =====
        if action == "accept":
            demo.status = "accepted"
            demo.save()

            details = {
                "Company": demo.company,
                "Scheduled Date": demo.scheduled_date.strftime("%Y-%m-%d %H:%M") if demo.scheduled_date else "N/A",
                "Phone": demo.phone,
            }

            # SEND ACCEPTANCE EMAIL
            send_expert_accept_email(
                demo.email,
                demo.name,
                expert.full_name or expert.username,
                "Demo Request",
                details
            )

            messages.success(request, "Demo request accepted and email sent to customer.")
            return redirect("expert_assigned_demos")

        # ===== REJECT DEMO =====
        elif action == "reject":
            reason = request.POST.get("reject_reason", "").strip()

            demo.status = "rejected"
            demo.expert_reject_reason = reason
            demo.save()

            details = {
                "Company": demo.company,
                "Scheduled Date": demo.scheduled_date.strftime("%Y-%m-%d %H:%M") if demo.scheduled_date else "N/A",
                "Phone": demo.phone,
                "Reason": reason,
            }

            # SEND REJECTION EMAIL
            send_expert_rejection_email(
                demo.email,
                demo.name,
                expert.full_name or expert.username,
                "Demo Request",
                details
            )

            messages.error(request, "Demo request rejected and email sent to customer.")
            return redirect("expert_assigned_demos")

    return render(request, "website/expert_assigned_demos.html", {
        "assigned_demos": assigned_demos
    })



logger = logging.getLogger(__name__)
@require_GET
def preview_job_application(request, application_id):
    """
    Return flat JSON expected by the frontend.
    Now correctly handles FloatField experience values.
    """
    try:
        app = get_object_or_404(JobApplication, id=application_id)

        # =============================
        # EXPERIENCE HANDLING (FloatField)
        # =============================
        exp = getattr(app, "experience_years", None)

        if exp is None:
            experience_text = "—"
            experience_source = "none"
        else:
            try:
                exp = float(exp)
                if exp == 0:
                    experience_text = "Fresher"
                    experience_source = "float"
                elif exp.is_integer():
                    experience_text = f"{int(exp)} year" if int(exp) == 1 else f"{int(exp)} years"
                    experience_source = "float_int"
                else:
                    experience_text = f"{exp} years"
                    experience_source = "float_decimal"
            except:
                # fallback if something unexpected
                experience_text = str(exp)
                experience_source = "fallback"

        # =============================
        # GRADUATION PERCENTAGE / CGPA
        # =============================
        gp = getattr(app, "graduation_percentage", None)
        if gp in (None, ""):
            cgpa_or_percent = "—"
        else:
            try:
                gp_val = float(gp)
                if gp_val > 10:
                    cgpa_or_percent = f"{round(gp_val, 2)}%"
                else:
                    cgpa_or_percent = str(gp_val)
            except:
                cgpa_or_percent = str(gp)

        # =============================
        # ATTACHMENT URL
        # =============================
        attachment_url = None
        try:
            if getattr(app, "attachment", None) and hasattr(app.attachment, "url"):
                attachment_url = request.build_absolute_uri(app.attachment.url)
        except Exception as exc:
            logger.exception("Error preparing attachment_url for job app %s: %s", application_id, exc)
            attachment_url = None

        # =============================
        # RESPONSE JSON
        # =============================
        response_data = {
            "full_name": getattr(app, "full_name", "") or "",
            "email": getattr(app, "email", "") or "",
            "phone": getattr(app, "phone", "") or "",
            "graduation_year": getattr(app, "graduation_year", "") or "",
            "graduation_percentage": cgpa_or_percent,

            "experience_years": experience_text,
            "experience_source": experience_source,
            "raw_experience": getattr(app, "experience_years", None),

            "key_skills": getattr(app, "key_skills", "") or "",
            "preferred_domain": (
                app.get_preferred_domain_display()
                if hasattr(app, "get_preferred_domain_display")
                else (getattr(app, "preferred_domain", "") or "")
            ),
            "cover_letter": getattr(app, "cover_letter", "") or "",
            "attachment_url": attachment_url,
            "id": app.id,
        }

        return JsonResponse(response_data)

    except JobApplication.DoesNotExist:
        return JsonResponse({"error": "Application not found"}, status=404)
    except Exception as e:
        logger.exception("preview_job_application error for id=%s: %s", application_id, e)
        return JsonResponse({"error": "Unexpected server error"}, status=500)





@login_required(login_url='admin_login')
def manage_candidates(request):
    """
    Admin view to list all registered candidates and their details.
    """
    candidates = CandidateProfile.objects.select_related('user').order_by('-created_at')

    return render(request, 'website/manage_candidates.html', {
        'candidates': candidates
    })

#  CANDIDATE OTP VERIFICATION 
def candidate_otp_verify(request):
    user_id = request.session.get('candidate_user_id')
    if not user_id:
        messages.warning(request, "Please register or log in to verify your account.")
        return redirect('candidate_login')

    try:
        user = User.objects.get(pk=user_id)
        profile = CandidateProfile.objects.get(user=user)
    except (User.DoesNotExist, CandidateProfile.DoesNotExist):
        messages.error(request, "Verification session expired or account not found.")
        return redirect('candidate_register')

    # If already verified
    if user.is_active:
        request.session.pop('candidate_user_id', None)
        messages.info(request, "Your account is already verified. Please log in.")
        return redirect('candidate_login')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            submitted = form.cleaned_data['otp_code'].strip()
            ok, msg = verify_otp(profile, submitted, expiry_minutes=5)

            if ok:
                # Activate user
                user.is_active = True
                user.save(update_fields=['is_active'])

                # Clear session
                request.session.pop('candidate_user_id', None)

                # Auto-login logic (keep this as you added)
                temp_pw = request.session.pop('temp_password', None)
                if temp_pw:
                    auth_user = authenticate(request, username=user.username, password=temp_pw)
                    if auth_user:
                        login(request, auth_user)

                # ⭐ CHANGE HERE → Redirect to candidate login with success message
                messages.success(request, "🎉 Registration successful! Please log in to continue.")
                return redirect('candidate_login')

            else:
                messages.error(request, msg or "Invalid or expired verification code.")
        else:
            messages.error(request, "Please enter a 6-digit code.")
    else:
        form = OTPVerificationForm()

    return render(request, 'website/otp_verify.html', {
        'form': form,
        'email': user.email,
        'role': 'Candidate'
    })

def expert_otp_verify(request):
    """
    Handles OTP verification for expert registration before allowing login.
    Adds validation for missing or expired OTPs and supports encrypted OTP comparison.
    """
    expert_id = request.session.get('expert_id_unverified')

    if not expert_id:
        messages.warning(request, "Please log in to verify your expert account.")
        return redirect('expert_login')

    try:
        expert = Expert.objects.get(pk=expert_id)
    except Expert.DoesNotExist:
        messages.error(request, "Verification session expired or expert account not found.")
        return redirect('expert_register')

    if not expert.otp_code:
        messages.info(request, "Your expert account is already verified. Please log in.")
        return redirect('expert_login')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code'].strip()

            if not expert.otp_created_at:
                messages.error(request, "OTP timestamp missing. Please request a new one.")
                return redirect('expert_register')

            otp_expiry = timezone.now() - timezone.timedelta(minutes=5)

            try:
                decrypted_otp = decrypt_data(expert.otp_code)
            except Exception:
                decrypted_otp = expert.otp_code 

            if decrypted_otp == otp_code and expert.otp_created_at > otp_expiry:
                expert.otp_code = None
                expert.otp_created_at = None
                expert.status = 'pending'  
                expert.save()

                request.session.pop('expert_id_unverified', None)

                messages.success(request, "Your expert account has been verified. Please wait for admin approval before logging in.")
                return redirect('expert_login')
            else:
                messages.error(request, "Invalid or expired OTP. Please try again.")
        else:
            messages.error(request, "Please enter a valid 6-digit code.")
    else:
        form = OTPVerificationForm()

    return render(request, 'website/otp_verify.html', {
        'form': form,
        'email': decrypt_data(expert.email),
        'role': 'Expert'
    })

#  CANDIDATE OTP RESEND 
def candidate_resend_otp(request):
    """Resends the OTP to the candidate."""
    user_id = request.session.get('candidate_user_id')
    if not user_id:
        messages.warning(request, "Session expired. Please log in again to verify.")
        return redirect('candidate_login')

    try:
        user = User.objects.get(pk=user_id)
        profile = CandidateProfile.objects.get(user=user)
    except (User.DoesNotExist, CandidateProfile.DoesNotExist):
        messages.error(request, "Account information missing. Please register again.")
        return redirect('candidate_register')

    user_name = f"{user.first_name} {user.last_name}"
    if generate_and_send_otp(profile, user.email, user_name, "Candidate"):
        messages.success(request, f" New verification code sent to {user.email}. Check your inbox!")
    else:
        messages.error(request, " Failed to resend OTP. Please try again later.")

    return redirect('candidate_otp_verify')

#  EXPERT OTP RESEND 
def expert_resend_otp(request):
    """Resends the OTP to the expert."""
    expert_id = request.session.get('expert_id_unverified')
    if not expert_id:
        messages.warning(request, "Session expired. Please log in again to verify.")
        return redirect('expert_login')

    try:
        expert = Expert.objects.get(pk=expert_id)
    except Expert.DoesNotExist:
        messages.error(request, "Expert account information missing. Please register again.")
        return redirect('expert_register')

    user_name = expert.full_name or expert.username
    if generate_and_send_otp(expert, expert.email, user_name, "Expert"):
        messages.success(request, f" New verification code sent to {expert.email}. Check your inbox!")
    else:
        messages.error(request, " Failed to resend OTP. Please try again later.")

    return redirect('expert_otp_verify')


# ABOUT OUR STORY 
@login_required(login_url='admin_login')
def about_our_story(request):
    about = AboutUs.objects.first()
    return render(request, 'website/about_our_story.html', {'about': about})

def admin_required(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(admin_required, login_url='admin_login')
def manage_about_us(request):
    about, created = AboutUs.objects.get_or_create(id=1)

    if request.method == 'POST':
        form = AboutUsForm(request.POST, instance=about)
        if form.is_valid():
            form.save()
            messages.success(request, "About Us section updated successfully.")
            return redirect('manage_about_us')
    else:
        form = AboutUsForm(instance=about)

    return render(request, 'website/manage_about_us.html', {'form': form})

def about_our_story(request):
    about = AboutUs.objects.first()
    return render(request, 'website/about_our_story.html', {'about': about})


# Manage Our Values
@login_required(login_url='admin_login')
def manage_our_values(request):
    values = CompanyValue.objects.all().order_by('order', 'created_at')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        icon = request.POST.get('icon', '')
        order = request.POST.get('order', 0)
        is_active = request.POST.get('is_active') == 'on'

        CompanyValue.objects.create(
            title=title,
            description=description,
            icon=icon,
            order=order,
            is_active=is_active
        )
        messages.success(request, 'New value added successfully!')
        return redirect('manage_our_values')

    return render(request, 'website/manage_our_values.html', {'values': values})

@login_required(login_url='admin_login')
def edit_our_value(request, pk):
    value = get_object_or_404(CompanyValue, pk=pk)

    if request.method == "POST":
        value.title = request.POST.get('title')
        value.description = request.POST.get('description')
        value.icon = request.POST.get('icon', '')
        value.order = request.POST.get('order', 0)
        value.is_active = request.POST.get('is_active') == 'on'

        value.save()
        messages.success(request, f'Value "{value.title}" updated successfully!')
        return redirect('manage_our_values')

    return render(request, 'website/edit_our_value.html', {'value': value})

@login_required(login_url='admin_login')
def delete_our_value(request, pk):
    value = get_object_or_404(CompanyValue, pk=pk)
    if request.method == "POST":
        title = value.title
        value.delete()
        messages.error(request, f'Value "{title}" has been deleted successfully.')
        return redirect('manage_our_values')
    return render(request, 'website/delete_our_value_confirm.html', {'value': value})

@login_required(login_url='admin_login')
def toggle_value_status(request, pk):
    value = get_object_or_404(CompanyValue, pk=pk)
    value.is_active = not value.is_active
    value.save()

    status = "activated" if value.is_active else "deactivated"
    messages.success(request, f'Value "{value.title}" has been {status}.')
    return redirect('manage_our_values')

def our_values(request):
    values = CompanyValue.objects.filter(is_active=True).order_by('order', 'created_at')
    return render(request, 'website/our_values.html', {'values': values})



@login_required(login_url='admin_login')
def manage_expert_registrations(request):
    """
    Display all expert registration requests for admin approval.
    When admin approves or rejects, sends an email notification to the expert.
    """

    experts = Expert.objects.all().order_by('-id')

    if request.method == 'POST':
        expert_id = request.POST.get('expert_id')
        action = request.POST.get('action')
        reason = request.POST.get('reason', '').strip()

        expert = get_object_or_404(Expert, id=expert_id)

        # --- APPROVAL HANDLER ---
        if action == 'approve':
            expert.status = 'approved'
            expert.otp_code = None
            expert.otp_created_at = None
            expert.is_verified = True
            expert.save()

            try:
                send_expert_status_email(expert, "approved")
                messages.success(
                    request,
                    f"{expert.full_name or expert.username} has been approved successfully, and a confirmation email has been sent."
                )
            except Exception as e:
                messages.warning(
                    request,
                    f"{expert.full_name or expert.username} was approved, but email sending failed: {e}"
                )

        # --- REJECTION HANDLER ---
        elif action == 'reject':
            expert.status = 'rejected'
            expert.is_verified = False
            expert.save()

            try:
                send_expert_status_email(expert, "rejected", reason)
                messages.error(
                    request,
                    f"{expert.full_name or expert.username}'s registration has been rejected. Email notification sent."
                )
            except Exception as e:
                messages.warning(
                    request,
                    f"{expert.full_name or expert.username}'s registration rejected, but email sending failed: {e}"
                )

        return redirect('manage_expert_registrations')

    return render(request, 'website/manage_expert_registrations.html', {
        'experts': experts
    })




logger = logging.getLogger(__name__)

def send_expert_status_email(expert, status, reason=None):
    """
    Sends approval or rejection email to an expert.
    status = "approved" or "rejected"
    reason = rejection message (optional)
    """

    user_name = expert.full_name or expert.username

    if status == "approved":
        subject = "Your Expert Registration Has Been Approved"
        template = "website/expert_approval_email.html"
        context = {
            "user_name": user_name,
            "submission_type": "Expert Registration Approved",
            "details": {
                "Status": "Approved",
                "Message": "Your expert account has been successfully approved."
            },
            "site_url": settings.DEFAULT_SITE_URL,
        }

    elif status == "rejected":
        subject = "Your Expert Registration Has Been Rejected"
        template = "website/expert_reject_email.html"
        context = {
            "user_name": user_name,
            "submission_type": "Expert Registration Rejected",
            "details": {
                "Status": "Rejected",
                "Reason": reason or "No reason provided."
            },
            "site_url": settings.DEFAULT_SITE_URL,
        }

    else:
        return False  # Unknown status

    # Render email content
    html_message = render_to_string(template, context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [expert.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send expert status email: {e}")
        return False



@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data=json.loads(request.body.decode("utf-8"))
            user_msg =data.get("message","").lower()

            qa_list = ChatbotQA.objects.all()
            for qa in qa_list:
                keywords=[k.strip().lower() for k in qa.keywords.split(",")]
                if any(k in user_msg for k in keywords):
                    return JsonResponse({"reply": qa.answer})
            return JsonResponse({"reply":"I'm still learning 🤖. Try asking something else!"})
        except Exception as e:
            return JsonResponse({"reply":"Server Error Occurred.."}, status=500)
    return JsonResponse({"reply":"Invalid Request.."},status=400)



# Manage our Team
@user_passes_test(admin_required, login_url='admin_login')
def manage_team(request):
    members = TeamMember.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '').strip()
        email = request.POST.get('email', '').strip()
        linkedin = request.POST.get('linkedin', '').strip()
        image = request.FILES.get('image')

        errors = []
        if not name:
            errors.append("Name is required.")
        if not position:
            errors.append("Position is required.")
        if email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors.append("Invalid email address.")
        if linkedin and not re.match(r'^https:\/\/(www\.)?linkedin\.com\/.+$', linkedin):
            errors.append("Invalid LinkedIn URL (must start with https://linkedin.com/).")
        if not image:
            errors.append("Please upload an image.")
        else:
            if image.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
                errors.append("Image must be JPG, PNG, or WEBP format.")
            if image.size > 5 * 1024 * 1024:
                errors.append("Image size must be under 5 MB.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'website/manage_team.html', {'members': members})

        TeamMember.objects.create(
            name=name,
            position=position,
            email=email,
            linkedin=linkedin,
            image=image
        )
        messages.success(request, " New team member added successfully!")
        return redirect('manage_team')

    return render(request, 'website/manage_team.html', {'members': members})


@user_passes_test(admin_required, login_url='admin_login')
def edit_member(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)

    if request.method == "POST":
        member.name = request.POST['name']
        member.position = request.POST['position']
        member.email = request.POST.get('email')
        member.linkedin = request.POST.get('linkedin')

        if 'image' in request.FILES:
            image = request.FILES['image']

            # Validate file extension (server-side protection)
            allowed_extensions = ['.jpg', '.jpeg', '.png']
            ext = os.path.splitext(image.name)[1].lower()

            if ext not in allowed_extensions:
                messages.error(request, "Only JPG and PNG images are allowed.")
                return redirect('manage_team')

            # Save the image only if valid
            member.image = image

        member.save()
        messages.success(request, f"{member.name} updated successfully!")

    return redirect('manage_team')

@user_passes_test(admin_required, login_url='admin_login')
def delete_member(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    if request.method == "POST":
        name = member.name
        member.delete()
        messages.success(request, f"{name} deleted successfully!")
    return redirect('manage_team')


def meet_the_team(request):
    members = TeamMember.objects.all().order_by('id')
    return render(request, 'website/meet_the_team.html', {'members': members})

# Join Our Mission
def join_our_mission(request):
    return render(request, 'website/join_our_mission.html')

# Manage Mission
def manage_mission(request):
    """
    View to add and manage missions.
    """
    if request.method == 'POST':
        form = MissionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mission added successfully!')
            return redirect('manage_mission') 
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MissionForm()

    missions = Mission.objects.all().order_by('-start_date')

    return render(request, 'website/manage_mission.html', {
        'form': form,
        'missions': missions,
        'now': timezone.now(),
    })


def join_our_mission(request):
    """
    Public page to display available missions.
    """
    missions = Mission.objects.filter(is_active=True).order_by('start_date')
    return render(request, 'website/join_our_mission.html', {
        'missions': missions,
        'now': timezone.now(),
    })

def edit_mission(request, pk):
    mission = get_object_or_404(Mission, pk=pk)
    if request.method == 'POST':
        form = MissionForm(request.POST, instance=mission)
        if form.is_valid():
            form.save()
            return redirect('manage_mission')
    else:
        form = MissionForm(instance=mission)
    return render(request,'website/edit_mission.html', {'form': form})


def delete_mission(request, pk):
    mission = get_object_or_404(Mission, pk=pk)
    mission.delete()
    messages.error(request, "Mission deleted successfully.")
    return redirect('manage_mission')




# PRIVACY POLICY
def privacy_policy(request):
    policies = PrivacyPolicy.objects.filter(is_active=True).order_by('-created_at')
    return render(request, "website/privacy_policy.html", {"policies": policies})


def manage_privacy(request):
    policies = PrivacyPolicy.objects.all().order_by('-created_at')
    form = PrivacyPolicyForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Privacy-policy updated  successfully.")
        return redirect("manage_privacy")

    return render(request, "website/manage_privacy.html", {"form": form, "policies": policies})


def edit_privacy(request, pk):
    policy = get_object_or_404(PrivacyPolicy, pk=pk)
    form = PrivacyPolicyForm(request.POST or None, instance=policy)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Privacy-policy edited  successfully.")
        return redirect("manage_privacy")

    return render(
        request,
        "website/manage_privacy.html",
        {"form": form, "policies": PrivacyPolicy.objects.all().order_by('-created_at')}
    )


def delete_privacy(request, pk):
    policy = get_object_or_404(PrivacyPolicy, pk=pk)
    policy.delete()
    messages.error(request, "Privacy-policy deleted successfully.")
    return redirect("manage_privacy")


def toggle_privacy_status(request, pk):
    policy = get_object_or_404(PrivacyPolicy, pk=pk)
    policy.is_active = not policy.is_active
    policy.save()
    return redirect("manage_privacy")


# TERMS & CONDITIONS

def terms_of_service(request):
    terms_list = TermsAndConditions.objects.filter(is_active=True).order_by('-created_at')
    return render(request, "website/terms_of_service.html", {"terms_list": terms_list})


def manage_terms(request):
    terms = TermsAndConditions.objects.all().order_by('-created_at')
    form = TermsAndConditionsForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Terms & Condition updated successfully")
        return redirect("manage_terms")

    return render(request, "website/manage_terms.html", {"form": form, "terms": terms})


def edit_terms(request, pk):
    term = get_object_or_404(TermsAndConditions, pk=pk)
    form = TermsAndConditionsForm(request.POST or None, instance=term)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Terms & Condition edited successfully")
        return redirect("manage_terms")

    return render(
        request,
        "website/manage_terms.html",
        {"form": form, "terms": TermsAndConditions.objects.all().order_by('-created_at')}
    )


def delete_terms(request, pk):
    term = get_object_or_404(TermsAndConditions, pk=pk)
    term.delete()
    messages.error(request, "Terms & Condition deleted successfully")
    return redirect("manage_terms")


def toggle_terms_status(request, pk):
    term = get_object_or_404(TermsAndConditions, pk=pk)
    term.is_active = not term.is_active
    term.save()
    return redirect("manage_terms")



# Encrpytion
def encrypt_decrypt_view(request):
    try:
        fernet = Fernet(settings.SECRET_ENCRYPTION_KEY)
    except Exception as e:
        return render(request, 'website/encrypt_decrypt.html', {'error': f"Key Initialization Error: {e}"})

    result = None
    original_data = ""
    error_message = None

    if request.method == 'POST':
        action = request.POST.get('action')
        data = request.POST.get('data', '').strip()
        original_data = data

        if not data:
            error_message = 'Data field cannot be empty.'
        
        else:
            try:
                if action == 'encrypt':
                    encoded_data = data.encode()
                    encrypted_data = fernet.encrypt(encoded_data)
                    result = encrypted_data.decode()
                    operation = "Encrypted"

                elif action == 'decrypt':
                    encrypted_token = data.encode()
                    decrypted_data = fernet.decrypt(encrypted_token)
                    result = decrypted_data.decode()
                    operation = "Decrypted"

            except Exception as e:
                error_message = f"Operation Failed. Check if the ciphertext is valid or the key is correct. Error: {e}"
                operation = "Failed"
        
        return render(request, 'website/encrypt_decrypt.html', {
            'original_data': original_data,
            'result': result,
            'operation': operation,
            'error_message': error_message,
        })

    return render(request, 'website/encrypt_decrypt.html',{})



            
# MANAGE PORTFOLIO
@login_required(login_url='admin_login')
def manage_portfolio(request):
    portfolios = Portfolio.objects.all().order_by('order')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        order = request.POST.get('order', 0)
        slug_value = slugify(title)
        image = request.FILES.get('image')

        Portfolio.objects.create(
            title=title,
            description=description,
            category=category,
            order=order,
            slug=slug_value,
            image=image
        )
        messages.success(request, "New portfolio item added successfully!")
        return redirect('manage_portfolio')

    return render(request, 'website/manage_portfolio.html', {'portfolios': portfolios})


@login_required(login_url='admin_login')
def edit_portfolio(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk)

    if request.method == 'POST':
        portfolio.title = request.POST.get('title')
        portfolio.description = request.POST.get('description')
        portfolio.category = request.POST.get('category')
        portfolio.order = request.POST.get('order', 0)
        slug_input = request.POST.get('slug')

        if slug_input and slug_input.strip().lower() != 'none':
            portfolio.slug = slug_input
        elif not portfolio.slug or portfolio.slug == 'None':
            portfolio.slug = slugify(portfolio.title)

        if 'image' in request.FILES:
            portfolio.image = request.FILES['image']

        portfolio.save()
        messages.success(request, "Portfolio updated successfully!")
        return redirect('manage_portfolio')

    return render(request, 'website/edit_portfolio.html', {'portfolio': portfolio})


@login_required(login_url='admin_login')
def delete_portfolio(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk)
    if request.method == "POST":
        portfolio.delete()
        messages.error(request, "Portfolio deleted successfully!")
        return redirect('manage_portfolio')
    return render(request, 'website/delete_portfolio.html', {'portfolio': portfolio})



class ExpertPasswordResetView(auth_views.PasswordResetView):
    template_name = 'website/expert_forgot_password.html'
    email_template_name = 'website/expert_password_reset_email.html'
    success_url = reverse_lazy('expert_password_reset_done')

    def post(self, request, *args, **kwargs):
        input_email = request.POST.get("email")

        # Fetch all matching experts
        experts = Expert.objects.filter(email__iexact=input_email)

        # Case 1: No expert found
        if not experts.exists():
            messages.error(request, "This email is not registered with any expert account.")
            return self.form_invalid(None)

        # Case 2: More than one expert found
        if experts.count() > 1:
            messages.error(
                request,
                "Multiple expert accounts found with this email. Please contact support."
            )
            return self.form_invalid(None)

        # Case 3: Exactly one expert → send reset link
        expert = experts.first()

        token = expert_token_generator.make_token(expert)
        uid = urlsafe_base64_encode(force_bytes(expert.pk))

        reset_url = request.build_absolute_uri(
            reverse_lazy('expert_password_reset_confirm',
                kwargs={'uidb64': uid, 'token': token}
            )
        )

        # Render HTML email
        html_message = render_to_string(self.email_template_name, {
            'user': expert,
            'username': expert.username,
            'uid': uid,
            'token': token,
            'reset_url': reset_url,
            'protocol': 'http',
            'domain': '127.0.0.1:8000',
        })

        # Send email
        msg = EmailMessage(
            subject="Propulsion Technology - Expert Password Reset",
            body=html_message,
            from_email="Propulsion Technology <Propulsiontech381@gmail.com>",
            to=[input_email],
        )
        msg.content_subtype = "html"
        msg.send()

        messages.success(
            request,
            "If this email exists, a password reset link has been sent."
        )
        return self.form_invalid(None)
    



# Simple form for password confirmation
class ExpertSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'}))

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("new_password1")
        pw2 = cleaned_data.get("new_password2")

        if pw1 != pw2:
            raise forms.ValidationError("Passwords do not match.")
        if len(pw1) < 6:
            raise forms.ValidationError("Password must be at least 6 characters long.")
        return cleaned_data


class ExpertPasswordResetConfirmView(FormView):
    template_name = "website/expert_password_reset_confirm.html"
    form_class = ExpertSetPasswordForm
    success_url = reverse_lazy("expert_password_reset_complete")

    def dispatch(self, request, *args, **kwargs):
        """Decode user ID from URL before form handling"""
        try:
            self.uid = force_str(urlsafe_base64_decode(self.kwargs.get("uidb64")))
            self.expert = Expert.objects.get(pk=self.uid)
        except (Expert.DoesNotExist, ValueError, TypeError, OverflowError):
            self.expert = None
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.expert:
            messages.error(self.request, "Invalid or expired password reset link.")
            return redirect("expert_password_reset")

        new_password = form.cleaned_data["new_password1"]
        self.expert.password = make_password(new_password)
        self.expert.save(update_fields=["password"])

        print(f" Password updated for expert: {self.expert.username}")
        messages.success(self.request, "Your password has been successfully reset.")
        return redirect(self.get_success_url())


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'website/job_detail.html', {'job': job})



def send_expert_status_email(expert, status, reason=None):
    expert_name = expert.full_name or expert.username
    login_url = settings.DEFAULT_SITE_URL + "/expert-login/"
    site_url = settings.DEFAULT_SITE_URL
    details = {
        "Username": expert.username,
        "Email": expert.email,
        "Status": status.capitalize(),
    }

    if status == "approved":
        subject = "✅ Expert Registration Approved - Propulsion Technology"
        html_message = render_to_string("website/expert_approved_email.html", {
            "expert_name": expert_name,
            "details": details,
            "login_url": login_url,
        })
    else:
        subject = "❌ Expert Registration Declined - Propulsion Technology"
        details["Reason"] = reason or "Not specified"
        html_message = render_to_string("website/expert_declined_email.html", {
            "expert_name": expert_name,
            "details": details,
            "site_url": site_url,
        })

    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [expert.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending expert status email to {expert.email}: {e}")
        return False
    



@login_required(login_url='admin_login')
def manage_feedback(request):
    feedbacks = ClientFeedback.objects.all().order_by('-created_at')
    form = ClientFeedbackForm()

    if request.method == 'POST':
        form = ClientFeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Feedback added successfully!")
            return redirect('manage_feedback')
        else:
            messages.error(request, "Please correct the errors below.")

    return render(request, 'website/manage_feedback.html', {
        'feedbacks': feedbacks,
        'form': form,
    })


@login_required(login_url='admin_login')
def edit_feedback(request, pk):
    feedback = get_object_or_404(ClientFeedback, id=pk)

    if request.method == "POST":
        client_name = request.POST.get("client_name", "").strip()
        fb_text = request.POST.get("feedback", "").strip()

        # ❌ Prevent empty values
        if not client_name:
            messages.error(request, "Client name cannot be empty.")
            return render(request, "website/edit_feedback.html", {"feedback": feedback})

        if not fb_text:
            messages.error(request, "Feedback cannot be empty.")
            return render(request, "website/edit_feedback.html", {"feedback": feedback})

        # If valid → save changes
        feedback.client_name = client_name
        feedback.feedback = fb_text
        feedback.save()

        messages.success(request, "Feedback updated successfully!")
        return redirect("manage_feedback")

    return render(request, "website/edit_feedback.html", {"feedback": feedback})





@login_required(login_url='admin_login')
def delete_feedback(request, pk):
    fb = get_object_or_404(ClientFeedback, pk=pk)
    fb.delete()
    messages.error(request, "Feedback deleted successfully!")
    return redirect('manage_feedback')



def admin_forgot_password(request):
    """
    Step 1: Accept admin email, generate OTP, and send email.
    """
    if request.method == "POST":
        email = request.POST.get('email', '').strip()

        try:
            admin_user = User.objects.get(email=email, is_superuser=True)
        except User.DoesNotExist:
            return render(request, 'website/admin_forgot_password.html', {
                'error': 'No admin account found with that email.'
            })

        otp = str(random.randint(100000, 999999))
        request.session['reset_admin_email'] = email
        request.session['reset_otp'] = otp
        request.session['otp_created'] = timezone.now().isoformat()
        request.session['otp_used'] = False

        # Email context
        context = {
            'username': admin_user.username,
            'user': admin_user,
            'otp': otp,
            'year': datetime.now().year,
            'site_url': getattr(settings, 'DEFAULT_SITE_URL', 'https://propulsiontech.in'),
        }

        html_message = render_to_string('website/admin_reset_otp_email.html', context)
        plain_message = strip_tags(html_message)
        subject = "Admin Password Reset OTP - Propulsion Technology"

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
        )

        return redirect('admin_verify_reset')

    return render(request, 'website/admin_forgot_password.html')


def admin_verify_reset(request):
    """
    Step 2: Verify OTP and reset password.
    """
    session_email = request.session.get('reset_admin_email')
    session_otp = request.session.get('reset_otp')
    otp_created = request.session.get('otp_created')
    otp_used = request.session.get('otp_used', False)

    # If session missing → redirect back
    if not (session_email and session_otp and otp_created):
        return redirect('admin_forgot_password')

    # Handle password reset
    if request.method == "POST":
        email = request.POST.get('email')
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Check OTP expiry (5 minutes)
        otp_time = timezone.datetime.fromisoformat(otp_created)
        if timezone.now() - otp_time > timedelta(minutes=5):
            request.session.flush()
            return render(request, 'website/admin_verify_reset.html', {
                'error': 'OTP expired. Please request a new one.'
            })

        if otp_used:
            return render(request, 'website/admin_verify_reset.html', {
                'error': 'This OTP has already been used. Request a new one.'
            })

        if otp != session_otp or email != session_email:
            return render(request, 'website/admin_verify_reset.html', {
                'error': 'Invalid OTP or email entered.'
            })

        if new_password != confirm_password:
            return render(request, 'website/admin_verify_reset.html', {
                'error': 'Passwords do not match.'
            })

        if len(new_password) < 8:
            return render(request, 'website/admin_verify_reset.html', {
                'error': 'Password must be at least 8 characters long.'
            })

        try:
            admin_user = User.objects.get(email=email, is_superuser=True)
            admin_user.set_password(new_password)
            admin_user.save()

            # Mark OTP used and clear session after success
            request.session['otp_used'] = True
            request.session.flush()

            messages.success(request, 'Password reset successful! Please log in with your new password.')
            return redirect('admin_login')

        except User.DoesNotExist:
            return render(request, 'website/admin_verify_reset.html', {
                'error': 'Admin not found.'
            })

    # GET request → show verification form
    return render(request, 'website/admin_verify_reset.html', {
        'success': f'OTP sent to {session_email}. Please check your inbox.'
    })


class CandidatePasswordResetView(auth_views.PasswordResetView):
    template_name = 'website/password_reset.html'
    email_template_name = 'website/password_reset_email.html'
    subject_template_name = 'website/password_reset_subject.txt'
    success_url = reverse_lazy('candidate_password_reset_done')

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")

        # Get all accounts with this email
        users = User.objects.filter(email__iexact=email)

        # Case 1: No user registered with this email
        if not users.exists():
            messages.error(request, "This email address is not associated with any account.")
            return self.form_invalid(None)

        # Case 2: Duplicate email (2 or more accounts)
        if users.count() > 1:
            messages.error(
                request,
                "Multiple accounts found with this email. Please contact support."
            )
            return self.form_invalid(None)

        # Case 3: Exactly one user → proceed with reset email
        user = users.first()

        # Generate reset token + uid
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = request.build_absolute_uri(
            reverse_lazy(
                'candidate_password_reset_confirm',
                kwargs={'uidb64': uid, 'token': token}
            )
        )

        # Render email HTML
        html_message = render_to_string(self.email_template_name, {
            'user': user,
            'uid': uid,
            'token': token,
            'reset_url': reset_url,
            'protocol': 'http',
            'domain': '127.0.0.1:8000'
        })

        # Send email
        email_obj = EmailMessage(
            subject="Propulsion Technology - Password Reset",
            body=html_message,
            from_email="Propulsion Technology <Propulsiontech381@gmail.com>",
            to=[email]
        )
        email_obj.content_subtype = "html"
        email_obj.send()

        messages.success(request, "Password reset link has been sent to your email.")
        return self.form_invalid(None)
    

def assign_project(request):
    if request.method == "POST":
        form = AssignProjectForm(request.POST, request.FILES)

        if form.is_valid():
            project = form.save()

            # --- SAVE BRIEF DOCUMENT IN BOTH MODELS ---
            brief_file = request.FILES.get("brief")
            if brief_file:
                # Save the brief inside Project model
                project.brief = brief_file
                project.save()

                # ALSO save it as an entry in ProjectDocument
                ProjectDocument.objects.create(
                    project=project,
                    attachment=brief_file
                )

            # --- CREATE PAYMENT ENTRY ---
            total = form.cleaned_data.get("amount_total") or 0
            paid = form.cleaned_data.get("amount_paid") or 0

            Payment.objects.create(
                project=project,
                amount_total=total,
                amount_paid=paid
            )

            messages.success(request, "Project assigned successfully!")
            return redirect("assign_project")

        else:
            print("FORM ERRORS:", form.errors)

    else:
        form = AssignProjectForm()

    return render(request, "website/assign_project.html", {"form": form})
                                                            

# Admin: list all assigned projects
from django.db.models import Q

def admin_project_list(request):
    projects = Project.objects.select_related("client__user").all().order_by("-id")

    # SEARCH
    search = request.GET.get("search")
    if search:
        projects = projects.filter(
            Q(project_name__icontains=search) |
            Q(client__user__username__icontains=search)
        )

    # FILTER BY CLIENT
    client_name = request.GET.get("client")
    if client_name and client_name != "None" and client_name.strip() != "":
        projects = projects.filter(
            client__user__username__icontains=client_name
        )

    # FILTER BY DATE
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date and end_date:
        projects = projects.filter(start_date__range=[start_date, end_date])

    return render(request, "website/admin_project_list.html", {
        "projects": projects,
        "search": search,
        "client": client_name,
        "start_date": start_date,
        "end_date": end_date,
    })


# Admin: show project details
def admin_project_details(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    history = PaymentRequest.objects.filter(project=project).order_by('-created_at')
    documents = ProjectDocument.objects.filter(project=project).order_by("-uploaded_at")
    payments = Payment.objects.filter(project=project).order_by("-payment_date")
    return render(request, "website/admin_project_details.html", {
        "project": project,
        "documents": documents,
        "payments": payments,
        "history": history,
    })



def payment_requests_list(request):
    requests_list = PaymentRequest.objects.order_by("-created_at")
    return render(request, "website/payment_requests_list.html", {
        "requests_list": requests_list
})


def payment_request_detail(request, req_id):
    pr = get_object_or_404(PaymentRequest, id=req_id)
    return render(request, "website/payment_request_detail.html", {
        "request_obj": pr
})


def approve_payment_request(request, req_id):
    pr = get_object_or_404(PaymentRequest, id=req_id)

    # 1) Update payment summary of the project
    payment, created = Payment.objects.get_or_create(project=pr.project)

    payment.amount_paid = float(payment.amount_paid) + float(pr.amount)
    payment.balance_amount = float(payment.amount_total) - float(payment.amount_paid)
    payment.save()

    # 2) Update request status
    pr.status = "Approved"
    pr.admin_reason = ""
    pr.save()

    messages.success(request, "Payment approved successfully.")
    return redirect("payment_requests_list")



def reject_payment_request(request, req_id):
    pr = get_object_or_404(PaymentRequest, id=req_id)

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()   # ✔ ALWAYS a string

        if not reason:
            messages.error(request, "Please enter reason for rejection.")
            return redirect("payment_request_detail", req_id=req_id)

        pr.status = "Rejected"
        pr.admin_reason = reason
        pr.save()

        messages.success(request, "Payment rejected successfully.")
        return redirect("payment_requests_list")

    return redirect("payment_request_detail", req_id=req_id)



def admin_add_payment(request, project_id):
    project = Project.objects.get(id=project_id)
    payment = Payment.objects.get(project=project)

    if request.method == "POST":

        # Convert to Decimal
        amount = Decimal(request.POST.get("amount"))
        mode = request.POST.get("mode")
        note = request.POST.get("note")

        # Create Payment Request (transaction history)
        PaymentRequest.objects.create(
            project=project,
            client=project.client,
            amount=amount,       # Decimal
            mode=mode,
            note=note,
            status="Approved",
            added_by_admin=True,
            admin_reason="Added by Admin"
        )

        # Update totals safely with Decimal
        payment.amount_paid += amount
        payment.balance_amount = payment.amount_total - payment.amount_paid
        payment.save()

        return redirect('admin_project_details', project_id=project.id)

    return render(request, 'website/admin_add_payment.html', {
        'project': project,
        'payment': payment,
    })


def admin_project_payment_list(request):
    from client.models import PaymentRequest
    payments = PaymentRequest.objects.all().order_by('-created_at')
    return render(request, 'website/admin_project_payment_list.html', {'payments': payments})



NAME_RE = re.compile(r'^[A-Za-z][A-Za-z ]{0,49}$')       
COMPANY_RE = re.compile(r'^[A-Za-z ]{1,50}$')           
PHONE_RE = re.compile(r'^[0-9]{10}$')                   


@login_required(login_url="admin_login")
def admin_client_register(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        company = (request.POST.get("company_name") or "").strip()
        address = (request.POST.get("address") or "").strip()
        password = (request.POST.get("password") or "")

        # ===== Required Field Checks =====
        if not name:
            messages.error(request, "Name is required.")
            return redirect("admin_client_register")

        if not email:
            messages.error(request, "Email is required.")
            return redirect("admin_client_register")

        if not phone:
            messages.error(request, "Phone number is required.")
            return redirect("admin_client_register")

        if not password:
            messages.error(request, "Password is required.")
            return redirect("admin_client_register")

        # ===== Name Validation =====
        if len(name) > 50 or not NAME_RE.match(name):
            messages.error(request, "Enter a valid name (letters and spaces only, up to 50 characters).")
            return redirect("admin_client_register")

        # ===== Email Validation =====
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Enter a valid email address.")
            return redirect("admin_client_register")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered")
            return redirect("admin_client_register")

        # ===== Phone Validation =====
        digits_only = re.sub(r'[^0-9]', '', phone)  # keep only digits

        if not PHONE_RE.match(digits_only):
            messages.error(request, "Phone must be exactly 10 digits.")
            return redirect("admin_client_register")

        phone = digits_only

        # === NEW: Phone uniqueness check ===
        if ClientProfile.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number is already registered")
            return redirect("admin_client_register")

        # ===== Company Validation (Optional) =====
        if company:
            if len(company) > 50 or not COMPANY_RE.match(company):
                messages.error(request, "Company name may contain only letters and spaces, up to 50 characters.")
                return redirect("admin_client_register")

        # ===== Address Validation (Optional) =====
        if address and len(address) > 300:
            messages.error(request, "Address must be 300 characters or fewer.")
            return redirect("admin_client_register")

        # ===== Password Validation =====
        if len(password) < 4 or len(password) > 20:
            messages.error(request, "Password must be between 4 and 20 characters.")
            return redirect("admin_client_register")

        # ===== Create User =====
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=name,
            password=password
        )

        # Ensure client is not staff / not superuser
        user.is_staff = False
        user.is_superuser = False
        user.save()

        # ===== Create Client Profile =====
        ClientProfile.objects.create(
            user=user,
            name=name,
            phone=phone,
            email=email,
            company_name=company,
            address=address,
            subject="Client Registration"
        )

        messages.success(request, "Client registered successfully!")
        return redirect("admin_client_register")

    return render(request, "website/admin_client_register.html")



# 1) LIST ALL CLIENTS
@login_required(login_url='admin_login')
def manage_clients(request):
    clients = (
        ClientProfile.objects
        .select_related('user')
        .filter(
            user__is_staff=False,       
            user__is_superuser=False    
        )
        .order_by('-id')
    )
    
    return render(request, 'website/manage_clients.html', {
        'clients': clients
})


@login_required(login_url='admin_login')
def client_detail(request, pk):
    client = get_object_or_404(ClientProfile, pk=pk)

    # All projects for this client
    projects = Project.objects.filter(client=client)

    # Payments for those projects
    payments = Payment.objects.filter(project__in=projects)

    # Totals
    total_amount = payments.aggregate(total=Sum('amount_total'))['total'] or 0
    paid_amount = payments.aggregate(total=Sum('amount_paid'))['total'] or 0

    # Remaining amount (never negative)
    remaining_amount = total_amount - paid_amount
    if remaining_amount < 0:
        remaining_amount = 0

    # -------------- AUTO STATUS LOGIC --------------
    # 1) No project assigned
    if not projects.exists():
        client.payment_status = "Not Assigned"

    # 2) Project exists and no dues left
    elif remaining_amount <= 0:
        client.payment_status = "Paid"

    # 3) Some amount paid, some due
    elif 0 < paid_amount < total_amount:
        client.payment_status = "Partial"

    # 4) Project has amount but nothing paid yet
    else:
        client.payment_status = "Pending"

    client.save(update_fields=["payment_status"])

    context = {
        "client": client,
        "projects": projects,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "remaining_amount": remaining_amount,
    }

    return render(request, 'website/client_detail.html', context)

# 3) EDIT CLIENT (basic inline edit of profile and user name/email)
@login_required(login_url='admin_login')
def edit_client(request, pk):
    client = get_object_or_404(ClientProfile, pk=pk)
    user = client.user

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        company = request.POST.get('company_name', '').strip()
        website = request.POST.get('website', '').strip()  # 👈 needed
        address = request.POST.get('address', '').strip()
        admin_notes = request.POST.get('admin_notes', '').strip()  # 👈 needed

        if not email:
            messages.error(request, 'Email is required.')
            return redirect('edit_client', pk=pk)

        user.first_name = name
        user.username = email
        user.email = email
        user.save()

        client.phone = phone
        client.company_name = company
        client.website = website        # <-- Now saves website
        client.address = address
        client.admin_notes = admin_notes  # <-- Now saves notes
        client.save()

        messages.success(request, "Client updated successfully!")
        return redirect('client_detail', pk=pk)  # RELOAD to show updated fields

    return render(request, 'website/edit_client.html', {"client": client})

# 4) DELETE CLIENT
@login_required(login_url='admin_login')
def delete_client(request, pk):
    client = get_object_or_404(ClientProfile, pk=pk)

    if request.method == "POST":
        # Delete user + client profile
        user = client.user
        client.delete()
        user.delete()

        messages.error(request, "Client deleted successfully.")
        return redirect('manage_clients')

    return redirect('manage_clients')



def admin_upload_document(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST" and request.FILES.get("document"):
        ProjectDocument.objects.create(
            project=project,
            attachment=request.FILES["document"],
            uploaded_by="admin",
            status="approved"
        )
        messages.success(request, "Project document uploaded successfully.")
        return redirect("admin_project_details", project_id=project.id)

    return redirect("admin_project_details", project.id)


def approve_document(request, doc_id):
    doc = get_object_or_404(ProjectDocument, id=doc_id)
    doc.status = "approved"
    doc.rejection_reason = ""
    doc.save()
    messages.success(request, "Client uploaded document approved successfully.")
    return redirect("admin_project_details", doc.project.id)


def reject_document(request, doc_id):
    doc = get_object_or_404(ProjectDocument, id=doc_id)

    if request.method == "POST":
        reason = request.POST.get("reason")
        doc.status = "rejected"
        doc.rejection_reason = reason
        doc.save()

        messages.error(request, "Document rejected with reason.")
        return redirect("admin_project_details", doc.project.id)

    return render(request, "website/reject_document.html", {"doc": doc})