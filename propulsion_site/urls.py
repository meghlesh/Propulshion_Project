from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from website import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('website.urls')),  
    path('client/', include('client.urls')),  
    path('chatbot/', views.chatbot_api, name='chatbot_api'),
    path('crypto/', views.encrypt_decrypt_view, name='crypto'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
