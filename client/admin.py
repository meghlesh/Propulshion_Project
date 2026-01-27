from django.contrib import admin
from django.contrib import admin
from .models import ClientProfile, Project, Payment, PaymentRequest, ProjectDocument, PersonalDocument

admin.site.register(ClientProfile)
admin.site.register(Project)
admin.site.register(ProjectDocument)
admin.site.register(PersonalDocument)
admin.site.register(Payment)
admin.site.register(PaymentRequest)
