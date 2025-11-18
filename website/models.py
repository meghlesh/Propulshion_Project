from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils import timezone
from .fields import EncryptedTextField
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, FileExtensionValidator


# Candidate Profile
class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    first_name_legal = models.CharField("First Name (Legal)", max_length=100)
    middle_name = models.CharField("Middle Name", max_length=100, blank=True, null=True)
    last_name = models.CharField("Last Name", max_length=100)
    # CHANGE: Encrypt PII
    phone_number = models.CharField(max_length=10, blank=True, null=True)

    # CHANGE: Encrypt PII
    address_line1 = EncryptedTextField("Address Line 1") 
    country = models.CharField("Country", max_length=100)
    state = models.CharField("State", max_length=100)
    city = models.CharField("City", max_length=100)

    school = models.CharField("School / Institution", max_length=150, blank=True, null=True)

    # NOTE: otp_code will store the encrypted OTP (handled manually in views.py)
    otp_code = models.CharField(max_length=255, blank=True, null=True) # Increased size for ciphertext
    otp_created_at = models.DateTimeField(null=True, blank=True)
    
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    last_updated = models.DateTimeField("Last Updated", auto_now=True)

    class Meta:
        verbose_name = "Manage Candidate"
        verbose_name_plural = "Manage Candidates"
        ordering = ['-date_created']

    def _str_(self):
        return f"{self.user.username} - {self.first_name_legal} {self.last_name}"


# Expert
class Expert(models.Model):
    STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    full_name = EncryptedTextField(blank=True, null=True)
    email = EncryptedTextField(blank=True, null=True)

    otp_code = models.CharField(max_length=255, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unverified')

    def __str__(self):
        return self.full_name or self.username


# Service (No changes - non-sensitive marketing data)
class Service(models.Model):
    COLOR_CHOICES = [
        ('accent-green', 'Accent Green'),
        ('highlight-gold', 'Highlight Gold'),
        ('card-bg', 'Card Background'),
    ]

    title = models.CharField(max_length=50)
    description = models.TextField(max_length=100)
    full_description = models.TextField(null=True, blank=True, max_length=250)

    # icon → exactly one character (or blank)
    icon = models.CharField(max_length=10, blank=True, null=True)

    color = models.CharField(max_length=50, choices=COLOR_CHOICES, default='accent-green')
    image = models.ImageField(upload_to='service_images/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    slug = models.SlugField(blank=True, null=True)

    def clean(self):
        """Model-level validation."""
        super().clean()
        # Title length is enforced by max_length, but we keep a friendly check
        if self.title and len(self.title) > 50:
            raise ValidationError({'title': 'Title must be 50 characters or fewer.'})

        if self.description and len(self.description) > 100:
            raise ValidationError({'description': 'Short description must be 100 characters or fewer.'})

        if self.full_description and len(self.full_description) > 250:
            raise ValidationError({'full_description': 'Full description must be 250 characters or fewer.'})

        # Icon must be exactly 1 character if present
        if self.icon:
            # Some emoji may be multiple code points; enforce length on the string value
            if len(self.icon) != 1:
                raise ValidationError({'icon': 'Icon must be exactly one character long.'})

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        # Run validation to prevent bad data from being saved anywhere
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

# Contact Form

def validate_file_size(file):
    max_bytes = 5 * 1024 * 1024  # 5 MB
    if file.size > max_bytes:
        raise ValidationError("Attachment size cannot exceed 5 MB.")

class ContactMessage(models.Model):
    name = models.CharField(
        max_length=15,
        validators=[MaxLengthValidator(15)],
    )
    email = models.EmailField()
    subject = models.CharField(
        max_length=100,
        validators=[MaxLengthValidator(100)],
    )
    message = EncryptedTextField(
        validators=[MaxLengthValidator(500)],
        help_text="Max 500 characters (stored encrypted)."
    )
    attachment = models.FileField(
        upload_to="contact_attachments/",
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "docx"]),
            validate_file_size
        ],
        blank=True,
        null=True,
        help_text="Optional. PDF or DOCX only. Max 5 MB."
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    def clean(self):
        # extra safeguard
        super().clean()
        if self.attachment:
            validate_file_size(self.attachment)


class ScheduleDemo(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('declined', 'Declined'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    scheduled_date = models.DateTimeField()
    # new field (non-editable, for DB-level uniqueness)
    scheduled_date_date = models.DateField(null=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_expert = models.ForeignKey('Expert', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        # Ensure scheduled_date_date is always synced with scheduled_date
        if self.scheduled_date:
            # If scheduled_date is timezone-aware, date() returns local date according to the datetime value;
            # this stores the calendar date portion.
            self.scheduled_date_date = self.scheduled_date.date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
    
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['email', 'phone', 'scheduled_date_date', 'company'],
            name='unique_demo_per_day_email_phone_company'
        )
    ]



class Job(models.Model):
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=100, default='Remote')
    description = models.TextField()
    requirements = models.TextField(blank=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def _str_(self):
        return self.title


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    # --- Job & Candidate Relations ---
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)

    # --- Candidate Info ---
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    # CHANGE: Encrypt PII
    phone = EncryptedTextField(max_length=10, blank=True) 

    # --- Uploaded Documents ---
    resume = models.FileField(
        upload_to='resumes/',
        help_text="Upload your resume (PDF, DOC, DOCX, max 5 MB)"
    )
    # CHANGE: Encrypt private letter
    cover_letter = EncryptedTextField( 
        blank=True,
        help_text="Optional short cover letter or motivation statement"
    )
    attachment = models.FileField(
        upload_to='attachments/',
        blank=True,
        null=True,
        help_text="Optional supporting document (PDF, DOC, DOCX, max 5 MB)"
    )

    graduation_year = models.IntegerField(default=2024)
    graduation_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    experience_years = models.FloatField(blank=True, null=True)

    # CHANGE: Encrypt key skills (personal info)
    key_skills = EncryptedTextField(default='')
    preferred_domain = models.CharField(
        max_length=100,
        choices=[
            ('data_analytics', 'Data Analytics'),
            ('ai_ml', 'AI / ML'),
            ('web_dev', 'Web Development'),
            ('automation', 'Business Process Automation'),
            ('finance', 'Finance & Reporting'),
            ('other', 'Other'),
        ],
        default='other'
    )

    # --- Status & Timestamps ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    applied_at = models.DateTimeField(auto_now_add=True)

    # --- String Representation ---
    def _str_(self):
        return f"{self.full_name} - {self.job.title}"


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    summary = models.TextField(help_text="A short summary for the blog listing page.")
    content = models.TextField()
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        from django.utils import timezone
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()
        super(BlogPost, self).save(*args, **kwargs)

    def _str_(self):
        return self.title


class ExpertQuery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('declined', 'Declined'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = EncryptedTextField(max_length=15, blank=True, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="expert_queries")
    message = EncryptedTextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    assigned_expert = models.ForeignKey('Expert', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # ⭐ ADD THIS FIELD ⭐
    decline_reason = models.TextField(null=True, blank=True)

    def _str_(self):
        return f"{self.name} - {self.service.title}"
    

class AboutUs(models.Model):
    title = models.CharField(max_length=200)
    mission = models.TextField()
    vision = models.TextField()
    story = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.title
    

class CompanyValue(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Emoji or icon class")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Company Value'
        verbose_name_plural = 'Company Values'

    def _str_(self):
        return self.title
    

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='team/', blank=True, null=True)

    def _str_(self):
        return self.name


class Mission(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def _str_(self):
        return self.title


class TermsAndConditions(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.title

from django.utils import timezone

class PrivacyPolicy(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)  
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.title
    


class Portfolio(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='portfolio_images/', blank=True, null=True)
    order = models.IntegerField(default=0)
    slug = models.SlugField(unique=True, max_length=255)

    class Meta:
        ordering = ['order']

    def _str_(self):
        return self.title
    

class ClientFeedback(models.Model):
    client_name = models.CharField(max_length=100)
    feedback = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Client Feedback"
        verbose_name_plural = "Client Feedbacks"
        ordering = ['-created_at']

    def _str_(self):
        return f"{self.client_name} - {self.feedback[:30]}"
    
#Chatbot Model

class ChatbotQA(models.Model):
    question = models.CharField(max_length=255)
    keywords = models.CharField(max_length=255, help_text="Comma-separated keywords")
    answer = models.TextField()

    def str(self):
        return self.question