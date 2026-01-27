"""
URL configuration for health check endpoints.
"""
from django.urls import path
from . import health

urlpatterns = [
    path('', health.HealthCheckView.as_view(), name='health_check'),
    path('ready/', health.ReadinessCheckView.as_view(), name='readiness_check'),
    path('live/', health.LivenessCheckView.as_view(), name='liveness_check'),
]
