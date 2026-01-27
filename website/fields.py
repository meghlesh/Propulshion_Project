from django.db import models
from .utils import encrypt_data, decrypt_data
import logging

logger = logging.getLogger(__name__)

class EncryptedTextField(models.TextField):
    """
    A temporary safe EncryptedTextField that gracefully skips encryption/decryption
    when the Fernet key is not configured.
    This prevents crashes (like during delete or query operations).
    """

    def get_db_prep_save(self, value, connection):
        """
        Encrypt the value before saving to the database — 
        only if a valid FERNET_CIPHER is configured.
        """
        try:
            from .utils import FERNET_CIPHER
            if not FERNET_CIPHER:
                # No encryption key configured — store as plain text
                logger.warning("⚠ No Fernet key found: saving as plain text.")
                return super().get_db_prep_save(value, connection)
        except Exception as e:
            logger.warning(f"⚠ Encryption skipped due to error: {e}")
            return super().get_db_prep_save(value, connection)

        # Normal encryption if cipher exists
        if value is not None:
            plaintext_value = str(value)
            # Prevent double encryption
            if not plaintext_value.startswith('gAAAAAB'):
                value = encrypt_data(plaintext_value)
        return super().get_db_prep_save(value, connection)

    def from_db_value(self, value, expression, connection):
        """
        Decrypt the value after loading from the database —
        only if Fernet is configured. Otherwise, return plain text.
        """
        try:
            from .utils import FERNET_CIPHER
            if not FERNET_CIPHER:
                return value  # skip decryption safely
        except Exception:
            return value

        # Decrypt only if value looks encrypted
        if value is not None and isinstance(value, str) and value.startswith('gAAAAAB'):
            try:
                value = decrypt_data(value)
            except Exception as e:
                logger.warning(f"⚠ Decryption skipped: {e}")
        return value

    def get_internal_type(self):
        """
        Django treats this as a normal TextField for migrations and admin usage.
        """
        return "TextField"