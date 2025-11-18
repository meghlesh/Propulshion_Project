from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import ScheduleDemo, JobApplication, ExpertQuery,CompanyValue, AboutUs, Mission, PrivacyPolicy, TermsAndConditions, ContactMessage, ClientFeedback
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
import re
import datetime
from .validators import validate_name, validate_cgpa, validate_graduation_year
from django.utils.timezone import is_naive, make_aware, get_current_timezone
from django.utils import timezone




# Admin Password Change

class AdminPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Old password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-highlight-gold focus:border-highlight-gold',
            'placeholder': 'Enter your current password'
        })
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-highlight-gold focus:border-highlight-gold',
            'placeholder': 'Enter new password (min 8 chars)'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-highlight-gold focus:border-highlight-gold',
            'placeholder': 'Confirm new password'
        })
    )

    def _init_(self, user, *args, **kwargs):
        """
        Expects the current user instance so we can validate old password.
        """
        super()._init_(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old = self.cleaned_data.get('old_password')
        if not self.user.check_password(old):
            raise forms.ValidationError("Old password is incorrect.")
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("New passwords do not match.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("New password must be at least 8 characters.")
        return cleaned

    def save(self, commit=True):
        """
        Set the new password on the user and save.
        """
        new_pw = self.cleaned_data['new_password1']
        self.user.set_password(new_pw)
        if commit:
            self.user.save()
        return self.user
#   CUSTOM VALIDATORS  

def validate_graduation_year(value):
    """Allow graduation year only between 2000 and 2026."""
    if value < 2000 or value > 2026:
        raise ValidationError("Graduation year must be between 2000 and 2026.")


def validate_name(value):
    """Ensure name has only alphabets and spaces."""
    if not re.match(r'^[A-Za-z\s]+$', value):
        raise ValidationError("Name should only contain letters and spaces.")


def validate_cgpa(value):
    """Ensure CGPA is between 0 and 10."""
    if value < 0 or value > 10:
        raise ValidationError("CGPA must be between 0 and 10.")


def validate_experience(value):
    """Restrict experience field to reasonable range."""
    if value:
        try:
            years = float(value)
            if years < 0 or years > 50:
                raise ValidationError("Experience must be between 0 and 50 years.")
        except ValueError:
            raise ValidationError("Experience must be a number (e.g., 2 or 2.5).")



class ScheduleDemoForm(forms.ModelForm):
    class Meta:
        model = ScheduleDemo
        fields = ['name', 'email', 'phone', 'company', 'message', 'scheduled_date']
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        phone = cleaned.get('phone')
        scheduled_dt = cleaned.get('scheduled_date')
        company = cleaned.get('company')  # <-- IMPORTANT

        if not (email and phone and scheduled_dt and company):
            return cleaned

        try:
            scheduled_date_only = scheduled_dt.date()
        except Exception:
            raise ValidationError("Invalid scheduled date provided.")

        # ❗ Block only if SAME EMAIL + SAME PHONE + SAME DATE + SAME SERVICE
        conflict_exists = ScheduleDemo.objects.filter(
            email__iexact=email.strip(),
            phone=phone.strip(),
            company__iexact=company.strip(),
            scheduled_date__date=scheduled_date_only
        ).exists()

        if conflict_exists:
            raise ValidationError(
                "You already scheduled a demo for this service on the same date."
            )

        return cleaned
class JobApplicationForm(forms.ModelForm):

    # =======================
    # Custom Form Fields
    # =======================
    full_name = forms.CharField(
        required=True,
        label="Full Name",
        strip=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'placeholder': 'Enter your full name (letters only)'
        })
    )

    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'placeholder': 'Enter your email (must contain @)'
        })
    )

    phone = forms.CharField(
        required=True,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'placeholder': 'Enter your 10-digit phone number'
        })
    )

    graduation_year = forms.IntegerField(
        required=True,
        label="Graduation Year",
        widget=forms.NumberInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'placeholder': 'e.g. 2023',
            'min': '2000',
            'max': str(datetime.date.today().year + 1)
        })
    )

    graduation_percentage = forms.DecimalField(
        required=True,
        max_digits=4,
        decimal_places=2,
        label="Graduation Percentage / CGPA",
        widget=forms.NumberInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'placeholder': 'e.g. 8.5',
            'min': '1',
            'max': '10',
            'step': '0.01'
        })
    )

    experience_years = forms.FloatField(
        required=False,
        label="Work Experience (in Years)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'placeholder': 'e.g. 2 or 2.5',
            'min': '0',
            'max': '50',
            'step': '0.1'
        })
    )

    key_skills = forms.CharField(
        required=True,
        label="Key Skills",
        widget=forms.TextInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'placeholder': 'e.g. Python, SQL, Excel, Power BI'
        })
    )

    preferred_domain = forms.ChoiceField(
        required=True,
        choices=[
            ('data_analytics', 'Data Analytics'),
            ('ai_ml', 'AI / ML'),
            ('web_dev', 'Web Development'),
            ('automation', 'Business Process Automation'),
            ('finance', 'Finance & Reporting'),
            ('other', 'Other'),
        ],
        label="Preferred Domain",
        widget=forms.Select(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full'
        })
    )

    resume = forms.FileField(
        required=True,
        label="Upload Resume (Max 5MB)",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'accept': '.pdf,.doc,.docx'
        })
    )

    cover_letter = forms.CharField(
        required=False,
        label="Cover Letter",
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control border rounded px-3 py-2 w-full',
            'placeholder': 'Write a short cover letter describing your motivation...'
        })
    )

    attachment = forms.FileField(
        required=False,
        label="Attach Cover Letter (Optional)",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control border rounded px-3 py-2 w-full',
            'accept': '.pdf,.doc,.docx'
        })
    )

    # ========================================
    # IMPORTANT: Allow auto-populated values to appear
    # ========================================
    def _init_(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super()._init_(*args, **kwargs)

        # Manually copy initial values for custom-declared fields
        for field in ['full_name', 'email', 'phone']:
            if field in initial:
                self.fields[field].initial = initial[field]

    # ===========================
    # MODEL & FIELDS
    # ===========================
    class Meta:
        model = JobApplication
        fields = [
            'full_name', 'email', 'phone', 'resume', 'cover_letter', 'attachment',
            'graduation_year', 'graduation_percentage',
            'experience_years', 'key_skills', 'preferred_domain'
        ]

    # ===========================
    # FIELD VALIDATION
    # ===========================
    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()

        if self.cleaned_data.get('full_name', '').startswith(' '):
            raise ValidationError("Name cannot start with a space.")

        if not re.match(r'^[A-Za-z]+(?: [A-Za-z]+)*$', name):
            raise ValidationError("Full name must contain only letters and single spaces.")

        return name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if '@' not in email:
            raise ValidationError("Email must contain '@'.")
        return email.lower()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not re.match(r"^\d{10}$", phone):
            raise ValidationError("Phone number must contain exactly 10 digits.")
        return phone

    def clean_graduation_year(self):
        year = self.cleaned_data.get('graduation_year')
        current_year = datetime.date.today().year

        if len(str(year)) != 4:
            raise ValidationError("Graduation year must be exactly 4 digits.")
        if year < 2000 or year > current_year + 1:
            raise ValidationError(f"Graduation year must be between 2000 and {current_year + 1}.")
        return year

def clean_graduation_percentage(self):
    val = self.cleaned_data.get('graduation_percentage')

    # Convert to Decimal safely
    try:
        num = Decimal(val)
    except:
        raise ValidationError("Enter a valid numeric value.")

    # Case 1: CGPA Range (0–10)
    if Decimal('0') <= num <= Decimal('10'):
        return num.quantize(Decimal('0.01'))

    # Case 2: Percentage Range (10–100)
    if Decimal('10') < num <= Decimal('100'):
        return num.quantize(Decimal('0.01'))

    # Otherwise invalid
    raise ValidationError("Enter a valid CGPA (0–10) or Percentage (10–100).")

def clean_experience(self):
    val = self.cleaned_data.get('experience_years')

    if val in (None, ""):
        return None

    try:
        years = float(val)
    except:
        raise ValidationError("Work experience must be a valid number.")

    if years < 0 or years > 50:
        raise ValidationError("Work experience must be between 0 and 50 years.")

    return round(years, 1)

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            if resume.size > 5 * 1024 * 1024:
                raise ValidationError("Resume must not exceed 5 MB.")
            if not resume.name.lower().endswith(('.pdf', '.doc', '.docx')):
                raise ValidationError("Only PDF, DOC, or DOCX files are allowed.")
        return resume

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if attachment.size > 5 * 1024 * 1024:
                raise ValidationError("Attachment must not exceed 5 MB.")
            if not attachment.name.lower().endswith(('.pdf', '.doc', '.docx')):
                raise ValidationError("Only PDF, DOC, or DOCX files are allowed.")
        return attachment

#   CANDIDATE REGISTER FORM  
class CandidateRegisterForm(forms.ModelForm):
    first_name_legal = forms.CharField(label="First Name (Legal) *", max_length=100, required=True, validators=[validate_name])
    middle_name = forms.CharField(label="Middle Name", max_length=100, required=False, validators=[validate_name])
    last_name = forms.CharField(label="Last Name *", max_length=100, required=True, validators=[validate_name])
    username = forms.CharField(label="Username *", max_length=100, required=True)
    preferred_email = forms.EmailField(label="Preferred Email *", required=True)
    phone_number = forms.CharField(label="Phone Number *", max_length=15, required=True)

    address_line1 = forms.CharField(label="Address Line 1 *", required=True, max_length=255)
    country = forms.CharField(label="Country *", required=True)
    state = forms.CharField(label="State *", required=True)
    city = forms.CharField(label="City *", required=True)
    school = forms.CharField(label="School / University *", max_length=150, required=True)

    password = forms.CharField(
        label="Password *",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password *",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'preferred_email', 'password']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()

        phone = re.sub(r'\D', '', phone)

        if not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if len(phone) < 10:
            raise ValidationError("Enter a valid 10-digit phone number.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        
        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
            
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
        
#   CANDIDATE LOGIN FORM  
class CandidateLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password'}))


#   OTP VERIFICATION FORM  
class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        label="Enter OTP",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-300 rounded-xl px-3 py-2 text-center text-xl tracking-wider',
            'placeholder': '••••••',
            'autofocus': 'autofocus',
            'inputmode': 'numeric', 
            'pattern': '[0-9]{6}',
            'maxlength': '6'
        })
    )


#   EXPERT QUERY FORM  
class ExpertQueryForm(forms.ModelForm):
    name = forms.CharField(validators=[validate_name])

    class Meta:
        model = ExpertQuery
        fields = ['name', 'email', 'phone', 'message']




# ABOUT US 
class AboutUsForm(forms.ModelForm):
    class Meta:
        model = AboutUs
        fields = ['title', 'mission', 'vision','story']

# COMPANY VALUE FORM 
class CompanyValueForm(forms.ModelForm):
    class Meta:
        model = CompanyValue
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 p-2 rounded-lg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 p-2 rounded-lg h-28'
            }),
        }


# Mission Form
from django import forms
from .models import Mission

class MissionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ['title', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'border-gray-300 rounded-lg p-2 w-full focus:ring-2 focus:ring-[#FF9728]'
            }),
            'title': forms.TextInput(attrs={'class': 'border-gray-300 rounded-lg p-2 w-full'}),
        }
        


class PrivacyPolicyForm(forms.ModelForm):
    class Meta:
        model = PrivacyPolicy
        fields = ['title', 'content', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-lg p-2'}),
            'content': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded-lg p-2', 'rows': 10}),
        }


class TermsAndConditionsForm(forms.ModelForm):
    class Meta:
        model = TermsAndConditions
        fields = ['title', 'content', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-lg p-2'}),
            'content': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded-lg p-2', 'rows': 10}),
        }

# Contact Message

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message", "attachment"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6}),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "") or ""
        if len(name) > 15:
            raise ValidationError("Name must be 15 characters or fewer.")
        return name

    def clean_subject(self):
        subject = self.cleaned_data.get("subject", "") or ""
        if len(subject) > 100:
            raise ValidationError("Subject must be 100 characters or fewer.")
        return subject

    def clean_message(self):
        message = self.cleaned_data.get("message", "") or ""
        if len(message) > 500:
            raise ValidationError("Message must be 500 characters or fewer.")
        return message

    def clean_attachment(self):
        attachment = self.cleaned_data.get("attachment")
        if attachment:
            ext = attachment.name.split(".")[-1].lower()
            if ext not in ("pdf", "docx"):
                raise ValidationError("Only PDF or DOCX files are allowed.")
            max_bytes = 5 * 1024 * 1024
            if attachment.size > max_bytes:
                raise ValidationError("Attachment size cannot exceed 5 MB.")
        return attachment
    

class ClientFeedbackForm(forms.ModelForm):
    class Meta:
        model = ClientFeedback
        fields = ['client_name', 'feedback']

    def clean_client_name(self):
        name = self.cleaned_data['client_name']
        if not re.match(r'^[A-Za-z\s]+$', name):
            raise forms.ValidationError("Client name can only contain letters and spaces.")
        return name.strip()

    def clean_feedback(self):
        fb = self.cleaned_data['feedback'].strip()
        if not re.match(r'^[A-Za-z\s.,!?]+$', fb):
            raise forms.ValidationError("Feedback should contain only letters and basic punctuation, no numbers.")
        return fb