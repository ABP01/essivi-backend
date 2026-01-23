"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication (Global)
    path('api/auth/', include('apps.users.urls_auth')), # We will create this file for cleaner separation
    path('', include('django_prometheus.urls')),
    
    # Old direct overrides if we don't want to create a new file, but creating a new file is cleaner. 
    # Let's try to just map them here for now to avoid creating files if possible, but apps.users.urls mixes everything.
    # Actually, let's keep it simple and just include the existing urls but strictly for the auth part? No, that pulls in the router.
    # Best approach: Add the specific paths here.
    
    # Authentication
    path('api/auth/login/', TokenObtainPairView.as_view(), name='auth_login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # Keep for compatibility
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='auth_token_refresh'),

    # App URLs
    path('api/users/', include('apps.users.urls')),
    path('api/logistics/', include('apps.logistics.urls')),
    path('api/sales/', include('apps.sales.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/reports/', include('apps.reports.urls')),

    # Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health checks
    path('health/', include('apps.dashboard.health_urls')),
]
