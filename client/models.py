from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError


def validate_file_size(file):
    max_bytes = 10 * 1024 * 1024 
    if file.size > max_bytes:
        raise ValidationError("File size cannot exceed 10 MB.")

# CLIENT PROFILE
class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")

    name = models.CharField(
        max_length=50, 
        validators=[MinLengthValidator(4), MaxLengthValidator(50)],
        verbose_name="Full Name",
        blank=True, 
        null=True
    )

    phone = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(10), MaxLengthValidator(20)],
        verbose_name="Phone Number",
        blank=True,
        null=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('Not Assigned', 'Not Assigned'),
            ('Paid', 'Paid'),
            ('Partial', 'Partial'),
            ('Pending', 'Pending'),
            ('Overdue', 'Overdue'),
        ],
        default='Not Assigned',
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    email = models.EmailField()
    subject = models.CharField(max_length=50)
    address = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(max_length=300, blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.company_name:
            return f"{self.company_name} ({self.user.username})"
        return self.name if self.name else self.user.username

    @property
    def remaining_amount(self):
        return float(self.total_amount) - float(self.paid_amount)

    @property
    def is_fully_paid(self):
        return self.remaining_amount <= 0


# PROJECT MODEL
class Project(models.Model):
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="projects",
        verbose_name="Client",
    )

    project_name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(3), MaxLengthValidator(100)],
        verbose_name="Project Name",
        blank=True,
        null=True
    )

    description = models.TextField(
        validators=[MinLengthValidator(10), MaxLengthValidator(1000)],
        verbose_name="Description",
        blank=True,
        null=True
    )

    deliverables = models.TextField(
    blank=True,
    null=True,
    verbose_name="Key Deliverables",
    help_text="Add each deliverable on a new line."
    )


    brief = models.FileField(
        upload_to="project_briefs/",
        blank=True,
        null=True,
        verbose_name="Project Brief Document",
        help_text="Upload PDF/DOCX (Optional)"
    )

    progress = models.IntegerField(
        default=0,
        verbose_name="Project Progress (%)",
        help_text="0 to 100"
)

    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date", blank=True, null=True)

    status = models.CharField(
        max_length=50,
        choices=[
            ("New", "New"),
            ("In Progress", "In Progress"),
            ("Completed", "Completed"),
        ],
        verbose_name="Status"
    )

    def __str__(self):
        return self.project_name or "Unnamed Project"


# PROJECT DOCUMENT MODEL
class ProjectDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to="project_docs/", null=True, blank=True)
    uploaded_by = models.CharField(
        max_length=20,
        choices=[("admin", "Admin"), ("client", "Client")],
        default="admin"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[("approved", "Approved"), ("pending", "Pending"), ("rejected", "Rejected")],
        default="approved"
    )

    rejection_reason = models.TextField(blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_name} - {self.attachment.name}"

    


# PERSONAL DOCUMENT MODEL
class PersonalDocument(models.Model):
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="personal_documents",
        verbose_name="Client"
    )

    attachment = models.FileField(
        upload_to="contact_attachments/",
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "docx", "jpg", "jpeg", "png"]),
            validate_file_size
        ],
        blank=True,
        null=True,
    )

    def _str_(self):
        return self.document_name


# PAYMENT MODEL — DEFAULT = 0 APPLIED (ENTERPRISE LOGIC)
class Payment(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="project_payments",
        verbose_name="Project"
    )

    amount_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Amount"
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Amount Paid"
    )

    balance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Balance Amount"
    )

    payment_date = models.DateField(auto_now_add=True, verbose_name="Payment Date")

    # ✅ Add Screenshot Upload Field
    screenshot = models.ImageField(
        upload_to="payment_screenshots/",
        blank=True,
        null=True,
        verbose_name="Payment Proof Screenshot"
    )

    def save(self, *args, **kwargs):
        self.balance_amount = float(self.amount_total) - float(self.amount_paid)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment for {self.project.project_name}"

    


# PAYMENT REQUEST MODEL — CLIENT → ADMIN APPROVAL FLOW
class PaymentRequest(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="payment_requests",
        verbose_name="Project"
    )
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="payment_requests",
        verbose_name="Client"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Payment Amount"
    )

    PAYMENT_MODES = [
        ("gpay", "Google Pay"),
        ("phonepe", "PhonePe"),
        ("paytm", "Paytm"),
        ("bank", "Bank Transfer"),
        ("cash", "Cash"),
        ("cheque", "Cheque"),
    ]
    mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODES,
        verbose_name="Payment Mode"
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Transaction / UTR / Cheque No."
    )

    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Note (optional)"
    )

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
        verbose_name="Status"
    )

    admin_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Admin Reason (if Rejected)"
    )
    
    added_by_admin = models.BooleanField(default=False)

    # ✅ ADD THIS FIELD
    screenshot = models.ImageField(
        upload_to="payment_screenshots/",
        null=True,
        blank=True,
        verbose_name="Payment Screenshot"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client} • {self.project} • {self.amount} ({self.status})"
    





