from django.urls import path
from . import views

app_name = "client"

urlpatterns = [
    path("login/", views.client_login, name="client_login"),
    path("dashboard/", views.client_dashboard, name="client_dashboard"),
    path('logout/', views.client_logout, name='client_logout'),

    # Project list
    path("projects/", views.client_projects, name="client_projects"),

    # Project details
    path("project/<int:project_id>/", views.client_project_details, name="client_project_details"),

    # Document upload
    path("project/<int:project_id>/upload-document/", views.upload_project_document, name="upload_project_document"),


    path("personal-docs/", views.client_personal_documents, name="client_personal_documents"),
    path("personal-docs/upload/", views.upload_personal_document, name="upload_personal_document"),
    path("personal-docs/<int:doc_id>/delete/", views.delete_personal_document, name="delete_personal_document"),


    # CLIENT PAYMENTS MODULE
    path("payments/", views.client_payments, name="client_payments"),
    path("payments/<int:project_id>/", views.client_project_payments, name="client_project_payments"),
    path("payments/<int:project_id>/make/", views.client_make_payment, name="client_make_payment"),
    path("payments/upload/<int:project_id>/", views.upload_payment_proof, name="upload_payment_proof"),
]