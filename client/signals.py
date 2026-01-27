from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import ClientProfile

# @receiver(post_save, sender=User)
# def create_client_profile(sender, instance, created, **kwargs):
#     # Only create profile for NON-staff, NON-superuser
#     if created and not instance.is_staff and not instance.is_superuser:
#         ClientProfile.objects.get_or_create(user=instance)


