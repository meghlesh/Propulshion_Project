# website/utils.py
import logging
from random import randint
from typing import Tuple, Optional
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# ---------------------------
# Fernet initialization
# ---------------------------
FERNET_KEY_RAW = None
# Prefer explicit FERNET_KEY but fall back to SECRET_ENCRYPTION_KEY for compatibility
if hasattr(settings, "FERNET_KEY") and settings.FERNET_KEY:
    FERNET_KEY_RAW = settings.FERNET_KEY
elif hasattr(settings, "SECRET_ENCRYPTION_KEY") and settings.SECRET_ENCRYPTION_KEY:
    FERNET_KEY_RAW = settings.SECRET_ENCRYPTION_KEY

FERNET_CIPHER: Optional[Fernet] = None
if FERNET_KEY_RAW:
    try:
        # Ensure bytes
        key_bytes = FERNET_KEY_RAW.encode() if isinstance(FERNET_KEY_RAW, str) else FERNET_KEY_RAW
        FERNET_CIPHER = Fernet(key_bytes)
        logger.info("Fernet cipher initialized.")
    except Exception as e:
        logger.critical(f"Failed to initialize Fernet cipher. Check FERNET_KEY/SECRET_ENCRYPTION_KEY. Error: {e}")
        FERNET_CIPHER = None
else:
    logger.warning("No FERNET_KEY or SECRET_ENCRYPTION_KEY configured. Encryption utilities will be no-ops.")


# ---------------------------
# Encryption helpers
# ---------------------------
def encrypt_data(plaintext_str: str) -> str:
    """
    Encrypt a plaintext string using the configured Fernet cipher.
    If no cipher is available, returns the original plaintext (with a logged warning).
    """
    if not plaintext_str:
        return plaintext_str
    if not FERNET_CIPHER:
        logger.warning("encrypt_data called but FERNET_CIPHER is not configured; returning plaintext.")
        return plaintext_str
    try:
        token = FERNET_CIPHER.encrypt(plaintext_str.encode("utf-8"))
        return token.decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return plaintext_str


def decrypt_data(ciphertext_str: str) -> str:
    """
    Decrypt a ciphertext string (produced by encrypt_data).
    If decryption fails or cipher not configured, returns the original ciphertext and logs a warning.
    """
    if not ciphertext_str:
        return ciphertext_str
    if not FERNET_CIPHER:
        logger.warning("decrypt_data called but FERNET_CIPHER is not configured; returning ciphertext.")
        return ciphertext_str
    try:
        plaintext = FERNET_CIPHER.decrypt(ciphertext_str.encode("utf-8"))
        return plaintext.decode("utf-8")
    except InvalidToken:
        logger.warning("decrypt_data failed: Invalid token or wrong key.")
        return ciphertext_str
    except Exception as e:
        logger.error(f"decrypt_data unexpected error: {e}")
        return ciphertext_str


# ---------------------------
# Email helper
# ---------------------------
def _send_otp_email(recipient_email: str, recipient_name: str, otp_code: str, role: str) -> bool:
    """
    Send OTP via email. Returns True on success, False on failure.
    """
    subject = f"{role} Account Verification - Propulsion Technology"

    # If you have an HTML template, render it. Otherwise fallback to plain text.
    try:
        html_message = render_to_string("website/otp_email.html", {
            "user_name": recipient_name,
            "otp_code": otp_code,
            "role": role,
        })
        plain_message = strip_tags(html_message)
    except Exception:
        plain_message = f"Hello {recipient_name},\n\nYour OTP for verification is: {otp_code}\nIt will expire in 5 minutes.\n\n- Propulsion Technology Team"
        html_message = None

    try:
        send_mail(subject, plain_message, getattr(settings, "DEFAULT_FROM_EMAIL", None), [recipient_email], html_message=html_message)
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {recipient_email}: {e}")
        return False


# ---------------------------
# OTP generation & verification
# ---------------------------

def generate_and_send_otp(model_instance, recipient_email: str, recipient_name: str, role: str) -> bool:
    """
    Generate a 6-digit OTP, encrypt it, save it on model_instance.otp_code and model_instance.otp_created_at,
    and send the plaintext OTP to recipient_email. Returns True if email was sent successfully.
    - model_instance: the model that will hold otp_code and otp_created_at fields (e.g., CandidateProfile).
    """
    if model_instance is None:
        logger.error("generate_and_send_otp called with None model_instance.")
        return False

    otp = f"{randint(100000, 999999):06d}"

    try:
        encrypted = encrypt_data(otp)
        # set fields (assumes model has otp_code and otp_created_at)
        setattr(model_instance, "otp_code", encrypted)
        setattr(model_instance, "otp_created_at", timezone.now())
        # Save with update_fields if possible
        try:
            model_instance.save(update_fields=["otp_code", "otp_created_at"])
        except Exception:
            model_instance.save()
    except Exception as e:
        logger.error(f"Failed to save OTP on model instance: {e}")
        return False

    # send plaintext OTP by email
    sent = _send_otp_email(recipient_email, recipient_name, otp, role)
    if not sent:
        logger.error(f"OTP generated but failed to send to {recipient_email}.")
    return sent


def verify_otp(model_instance, submitted_otp: str, expiry_minutes: int = 5) -> Tuple[bool, str]:
    """
    Verify the submitted_otp against the encrypted code stored on model_instance.
    Returns (True, message) on success, (False, message) on failure.

    On success this will clear model_instance.otp_code and model_instance.otp_created_at and save the instance.
    """
    if model_instance is None:
        return False, "Verification failed: internal error."

    stored_cipher = getattr(model_instance, "otp_code", None)
    created_at = getattr(model_instance, "otp_created_at", None)

    if not stored_cipher or not created_at:
        return False, "No verification code found. Please request a new code."

    # Trim whitespace from submitted OTP
    submitted = (submitted_otp or "").strip()
    if not submitted:
        return False, "Please enter the verification code."

    # Check expiry (timezone-aware)
    try:
        expiry_time = created_at + timedelta(minutes=expiry_minutes)
    except Exception:
        # be defensive if created_at isn't a datetime
        return False, "Verification timestamp invalid. Please request a new code."

    now = timezone.now()
    if now > expiry_time:
        return False, "Verification code expired. Please request a new code."

    # Decrypt stored cipher and compare
    try:
        decrypted = decrypt_data(stored_cipher)
    except Exception as e:
        logger.warning(f"OTP decryption error: {e}")
        return False, "Failed to verify code. Please request a new code."

    if str(decrypted).strip() == submitted:
        # Clear stored OTP and timestamp
        try:
            setattr(model_instance, "otp_code", None)
            setattr(model_instance, "otp_created_at", None)
            try:
                model_instance.save(update_fields=["otp_code", "otp_created_at"])
            except Exception:
                model_instance.save()
        except Exception as e:
            logger.error(f"Failed to clear OTP fields after successful verification: {e}")
            # still return success since code matched
        return True, "Verification successful."
    else:
        return False, "Invalid verification code."


# Optional convenience wrapper for resending
def resend_otp(model_instance, recipient_email: str, recipient_name: str, role: str) -> bool:
    """
    Generate a new OTP and send it again. Returns True if send succeeded.
    """
    return generate_and_send_otp(model_instance, recipient_email, recipient_name, role)



def send_confirmation_email(recipient_email, user_name, subject, details, cta_url=None):
    """
    Sends a confirmation email for demo scheduling.
    Returns True if the email was sent successfully, False otherwise.
    """
    try:
        # Build message body
        message = (
            f"Hi {user_name},\n\n"
            f"Thank you for scheduling a demo with Propulsion!\n\n"
            f"Here are your details:\n"
        )

        for key, value in details.items():
            message += f"{key}: {value}\n"

        if cta_url:
            message += f"\nYou can manage your demo here: {cta_url}\n"

        message += "\nBest regards,\nThe Propulsion Team"

        # Send the email
        send_mail(
            subject=f"Propulsion — {subject}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        return True

    except Exception as e:
        print(f"Error sending confirmation email: {e}")
    return False



class ExpertTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, expert, timestamp):
        # Avoid using last_login — only depend on PK and password
        return str(expert.pk) + expert.password + str(timestamp)

expert_token_generator = ExpertTokenGenerator()




def send_expert_rejection_email(
    client_email,
    client_name,
    expert_name,
    request_type,
    details
):

    subject = f"Your {request_type} Was Not Approved"

    html_message = f"""
    <div style="font-family:Poppins,sans-serif;background:#FDF4F4;padding:25px;">
        <div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:30px;box-shadow:0 4px 12px rgba(0,0,0,0.1)">
            
            <h2 style="color:#8B0000;margin-bottom:10px;">Hello {client_name},</h2>

            <p style="font-size:15px;color:#333;">
                We regret to inform you that your 
                <strong>{request_type}</strong> was 
                <span style="color:#C62828;font-weight:bold;">rejected</span> 
                by expert <strong>{expert_name}</strong>.
            </p>

            <div style="margin-top:20px;">
                <h3 style="color:#053830;">Details:</h3>
                <table width="100%" cellpadding="8" style="border-collapse:collapse;margin-top:10px;">
    """

    for key, value in details.items():
        html_message += f"""
            <tr>
                <td style="background:#FCE8E6;color:#8B0000;border-radius:8px 0 0 8px;font-weight:bold;width:35%;">{key}</td>
                <td style="background:#FFFFFF;border-radius:0 8px 8px 0;">{value}</td>
            </tr>
        """

    html_message += """
                </table>
            </div>

            <p style="margin-top:25px;color:#053830;">
                You may submit a new request or contact our team for further assistance.
            </p>

            <p style="margin-top:30px;text-align:center;color:#999;">
                © 2025 Propulsion Technology. All Rights Reserved.
            </p>

        </div>
    </div>
    """

    try:
        send_mail(
            subject=subject,
            message="Your request was rejected.",
            html_message=html_message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[client_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print("Error:", e)
        return False
    



def send_expert_accept_email(
    client_email,
    client_name,
    expert_name,
    request_type,
    details
):
    """
    Sends acceptance email to the customer when expert accepts
    a query or demo request.
    """

    subject = f"Your {request_type} Has Been Accepted 🎉"

    html_message = f"""
    <div style="font-family: Poppins, sans-serif; background:#F4F8F1; padding:25px;">
        <div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:30px;box-shadow:0 4px 12px rgba(0,0,0,0.1)">
            
            <h2 style="color:#053830;margin-bottom:10px;">Hello {client_name},</h2>

            <p style="font-size:15px;color:#053830;">
                Good news! Your <strong>{request_type}</strong> has been 
                <span style="color:#1E8F5C;font-weight:bold;">accepted</span> by expert 
                <strong>{expert_name}</strong>.
            </p>

            <div style="margin-top:20px;">
                <h3 style="color:#053830;">Request Details:</h3>
                <table width="100%" cellpadding="8" style="border-collapse:collapse;margin-top:10px;">
    """

    for key, value in details.items():
        html_message += f"""
            <tr>
                <td style="background:#EAF4E0;color:#053830;border-radius:8px 0 0 8px;font-weight:bold;width:35%;">{key}</td>
                <td style="background:#FFFFFF;border-radius:0 8px 8px 0;">{value}</td>
            </tr>
        """

    html_message += """
                </table>
            </div>

            <p style="margin-top:25px;color:#053830;">
                Thank you for choosing <strong>Propulsion Technology</strong>.<br>
                Our expert will contact you soon regarding the next steps.
            </p>

            <p style="margin-top:30px;text-align:center;color:#999">
                © 2025 Propulsion Technology. All Rights Reserved.
            </p>

        </div>
    </div>
    """

    try:
        send_mail(
            subject=subject,
            message="Your request has been accepted.",
            html_message=html_message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[client_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False