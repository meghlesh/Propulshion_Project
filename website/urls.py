from . import views 
from django.contrib.auth import views as auth_views
from django.shortcuts import render
from django.urls import path, reverse_lazy
from .views import ExpertPasswordResetView, CandidatePasswordResetView
from django.contrib import admin

from website.views import (
    expert_assigned_queries_view,
    expert_assigned_demos_view,
    ExpertPasswordResetConfirmView,
)

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('services/<slug:slug>/', views.service_detail, name='service_detail'),
    path('ask-expert/', views.ask_expert, name='ask_expert'),

    # 📰 BLOG 
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),

    # 🧑‍💼 ADMIN AUTH & DASHBOARD 
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # ⚙ ADMIN MANAGEMENT 
    ## Services
    path('dashboard/manage-services/', views.manage_services, name='manage_services'),
    path("services/", views.services, name="services"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path('dashboard/manage-services/edit/<int:pk>/', views.edit_service, name='edit_service'),
    path('dashboard/manage-services/delete/<int:pk>/', views.delete_service, name='delete_service'),

    ## Blog Posts
    path('dashboard/manage-blog-posts/', views.manage_blog_posts, name='manage_blog_posts'),
    path('dashboard/manage-blog-posts/edit/<int:pk>/', views.edit_blog_post, name='edit_blog_post'),
    path('dashboard/manage-blog-posts/delete/<int:pk>/', views.delete_blog_post, name='delete_blog_post'),
    
    ## Jobs and Applications
    path('careers/', views.careers_list, name='careers'),
    path('careers/', views.careers_list, name='careers_list'),
    path('jobs/<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('dashboard/manage-jobs/', views.manage_jobs, name='manage_jobs'),
    path('dashboard/manage-jobs/edit/<int:pk>/', views.edit_job, name='edit_job'),
    path('dashboard/manage-applications/', views.manage_applications, name='manage_applications'),
    path('dashboard/manage-applications/<int:application_id>/preview/', views.preview_job_application, name='preview_job_application'),
    path('dashboard/manage-candidates/', views.manage_candidates, name='manage_candidates'),

    ## Client / Demo / Query Management
    path('dashboard/manage-client-responses/', views.manage_client_responses, name='manage_client_responses'),
    path('dashboard/manage-expert-queries/', views.manage_expert_queries, name='manage_expert_queries'),
    path('dashboard/manage-assigned-queries/', views.manage_assigned_queries, name='manage_assigned_queries'),
    path('dashboard/manage-declined-queries/', views.manage_declined_queries, name='manage_declined_queries'),
    path('dashboard/manage-demo-requests/', views.manage_demo_requests, name='manage_demo_requests'),

    # 📅 SCHEDULE DEMO 
    path('schedule-demo/', views.schedule_demo, name='schedule_demo'),

    # 👩‍💻 CANDIDATE AUTH 
    path('candidate/register/', views.candidate_register, name='candidate_register'),
    path('candidate/login/', views.candidate_login, name='candidate_login'),
    path('candidate/logout/', views.candidate_logout, name='candidate_logout'),
    path('candidate/dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    path('candidate/logged-out/', views.candidate_logged_out_view, name='candidate_logged_out'),
    
    # OTP Verification for Candidate
    path('candidate/verify/', views.candidate_otp_verify, name='candidate_otp_verify'),
    path('candidate/resend/', views.candidate_resend_otp, name='candidate_resend_otp'),

    # 👨‍🏫 EXPERT AUTH & DASHBOARD 
    path('expert-login/', views.expert_login_view, name='expert_login'),
    path('expert-register/', views.expert_register_view, name='expert_register'),
    path('expert-dashboard/', views.expert_dashboard_view, name='expert_dashboard'),
    path('expert-logout/', views.expert_logout_view, name='expert_logout'),

    # NEW: Manage Expert Registrations (Admin Approval)
    path('dashboard/manage-expert-registrations/', views.manage_expert_registrations, name='manage_expert_registrations'),

    # Expert Assignments
    path('expert/queries/', expert_assigned_queries_view, name='expert_assigned_queries'),
    path('expert/demos/', expert_assigned_demos_view, name='expert_assigned_demos'),
    
    # OTP Verification for Experts
    path('expert/verify/', views.expert_otp_verify, name='expert_otp_verify'),
    path('expert/resend/', views.expert_resend_otp, name='expert_resend_otp'),

    # ABOUT & OUR VALUES  
    path('about-our-story/', views.about_our_story, name='about_our_story'),
    path('manage-about-us/', views.manage_about_us, name='manage_about_us'),

    # Meet the Team
    path('meet-the-team/', views.meet_the_team, name='meet_the_team'),
    path('manage-team/', views.manage_team, name='manage_team'),
    path('edit-member/<int:pk>/', views.edit_member, name='edit_member'),
    path('delete-member/<int:pk>/', views.delete_member, name='delete_member'),

    path('our-values/', views.our_values, name='our_values'),
    path('dashboard/manage-our-values/', views.manage_our_values, name='manage_our_values'),
    path('dashboard/manage-our-values/edit/<int:pk>/', views.edit_our_value, name='edit_our_value'),
    path('dashboard/manage-our-values/delete/<int:pk>/', views.delete_our_value, name='delete_our_value'),
    path('dashboard/manage-our-values/toggle/<int:pk>/', views.toggle_value_status, name='toggle_value_status'),


    path('dashboard/manage-portfolio/', views.manage_portfolio, name='manage_portfolio'),
    path('dashboard/manage-portfolio/edit/<int:pk>/', views.edit_portfolio, name='edit_portfolio'),
    path('dashboard/manage-portfolio/delete/<int:pk>/', views.delete_portfolio, name='delete_portfolio'),

    path('manage-privacy/', views.manage_privacy, name='manage_privacy'),
    path('manage-terms/', views.manage_terms, name='manage_terms'),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms-of-service/", views.terms_of_service, name="terms_of_service"),

    # --- DASHBOARD (Admin Custom) ---
    path("dashboard/manage-privacy/", views.manage_privacy, name="manage_privacy"),
    path("dashboard/manage-privacy/edit/<int:pk>/", views.edit_privacy, name="edit_privacy"),
    path("dashboard/manage-privacy/delete/<int:pk>/", views.delete_privacy, name="delete_privacy"),
    path("dashboard/manage-privacy/toggle/<int:pk>/", views.toggle_privacy_status, name="toggle_privacy_status"),

    path("dashboard/manage-terms/", views.manage_terms, name="manage_terms"),
    path("dashboard/manage-terms/edit/<int:pk>/", views.edit_terms, name="edit_terms"),
    path("dashboard/manage-terms/delete/<int:pk>/", views.delete_terms, name="delete_terms"),
    path("dashboard/manage-terms/toggle/<int:pk>/", views.toggle_terms_status, name="toggle_terms_status"),
  
    # Join our Mission 
    path('join-our-mission/', views.join_our_mission, name='join_our_mission'),
    path('manage-mission/', views.manage_mission, name='manage_mission'),
    path('edit-mission/<int:pk>/', views.edit_mission, name='edit_mission'),
    path('delete-mission/<int:pk>/', views.delete_mission, name='delete_mission'),

    # 💌 CANDIDATE PASSWORD RESET (fixed)
# CANDIDATE PASSWORD RESET (custom validation)
path(
    'candidate/password_reset/',
    CandidatePasswordResetView.as_view(),
    name='candidate_password_reset'
),

path(
    'candidate/password_reset_done/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='website/password_reset_done.html'
    ),
    name='candidate_password_reset_done'
),

path(
    'candidate/reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='website/password_reset_confirm.html',
        success_url=reverse_lazy('candidate_password_reset_complete')
    ),
    name='candidate_password_reset_confirm'
),

path(
    'candidate/reset/done/',
    auth_views.PasswordResetCompleteView.as_view(
        template_name='website/password_reset_complete.html'
    ),
    name='candidate_password_reset_complete'
),



    # 💼 EXPERT PASSWORD RESET (manual reset, same as candidate)
    path('expert/password_reset/', ExpertPasswordResetView.as_view(), name='expert_password_reset'),

    path('expert/password_reset_done/',
     auth_views.PasswordResetDoneView.as_view(template_name='website/expert_password_reset_done.html'),
     name='expert_password_reset_done'),

    path(
    'expert/reset/<uidb64>/<token>/',
    ExpertPasswordResetConfirmView.as_view(),
    name='expert_password_reset_confirm'
    ),

    path('expert/reset/done/',
     auth_views.PasswordResetCompleteView.as_view(template_name='website/expert_password_reset_complete.html'),
     name='expert_password_reset_complete'),

    # Job Detail
    path('job/<int:pk>/', views.job_detail, name='job_detail'),

    # DELETE JOB
    path('dashboard/manage-jobs/delete/<int:pk>/', views.delete_job, name='delete_job'),

    path('manage-jobs/', views.manage_jobs, name='manage_jobs'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),

    # Feedback management
    path('dashboard/manage-feedback/', views.manage_feedback, name='manage_feedback'),
    path('dashboard/manage-feedback/edit/<int:pk>/', views.edit_feedback, name='edit_feedback'),
    path('dashboard/manage-feedback/delete/<int:pk>/', views.delete_feedback, name='delete_feedback'),


    # 🔐 Admin password reset custom flow
    path('admin-panel/forgot-password/', views.admin_forgot_password, name='admin_forgot_password'),
    path('admin-panel/verify-reset/', views.admin_verify_reset, name='admin_verify_reset'),

    path(
    'application/confirmation/<int:application_id>/',
    views.application_confirmation,
    name='application_confirmation'
    ),


    # 🤖 CHATBOT
    path('chatbot/', views.chatbot_api, name='chatbot_api'),

        # keep this at the bottom
    path('admin/', admin.site.urls),
]