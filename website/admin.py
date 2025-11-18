from django.contrib import admin
from .models import Service, ContactMessage, Job, JobApplication, BlogPost, CandidateProfile
from .models import ChatbotQA

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'color', 'order')
    list_editable = ('order',)
    search_fields = ('title',)
    ordering = ('order',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at')
    readonly_fields = ('submitted_at',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'posted_at', 'is_active')
    search_fields = ('title', 'location')

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'job', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('full_name', 'email')

#  BLOG POST ADMIN ADDED 
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_date', 'created_at')
    list_filter = ('status', 'author')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)



@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name_legal', 'last_name', 'phone_number', 'city', 'state', 'date_created')
    search_fields = ('user__username', 'first_name_legal', 'last_name', 'phone_number')
    list_filter = ('state', 'city', 'date_created')
    ordering = ('-date_created',)


@admin.register(ChatbotQA)
class chatbotQAAdmin(admin.ModelAdmin):
    list_display = ("question","keywords")
    search_fields = ("question","keywords","answer")
