# website/validators.py
import re
from django.core.exceptions import ValidationError
from datetime import datetime

def validate_name(value):
    if not re.match(r'^[A-Za-z\s]+$', value):
        raise ValidationError("Name can contain only letters and spaces.")

def validate_cgpa(value):
    if value < 0 or value > 10:
        raise ValidationError("CGPA / Percentage must be between 0 and 10.")

def validate_graduation_year(value):
    current_year = datetime.now().year
    if value < 2000 or value > current_year + 1:
        raise ValidationError(f"Graduation year must be between 2000 and {current_year + 1}.")
