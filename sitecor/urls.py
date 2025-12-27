from django.contrib import admin
from django.urls import path, include
from aplicativo import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('aplicativo.urls')),
    path('admin/', admin.site.urls),
    path('video/', views.video_dashboard, name='video_dashboard'),
    path('api/cameras-proxy/', views.api_cameras_proxy, name='cameras_proxy'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
