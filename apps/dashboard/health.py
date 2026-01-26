"""
Health check and monitoring endpoints.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
import logging
from drf_spectacular.utils import extend_schema

logger = logging.getLogger('apps.dashboard')


@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(
    responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}, 'services': {'type': 'object'}}}},
    description="Health check endpoint"
)
def health_check(request):
    """
    Health check endpoint for monitoring.
    Returns 200 if all services are healthy.
    """
    health_status = {
        'status': 'healthy',
        'services': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['services']['database'] = 'unhealthy'
        health_status['status'] = 'degraded'
    
    # Check cache (if configured)
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['services']['cache'] = 'healthy'
        else:
            health_status['services']['cache'] = 'unhealthy'
    except Exception as e:
        logger.warning(f"Cache health check failed: {e}")
        health_status['services']['cache'] = 'not_configured'
    
    return Response(health_status)


@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(
    responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
    description="Readiness check"
)
def readiness_check(request):
    """
    Readiness check for Kubernetes/Docker.
    Returns 200 when app is ready to serve requests.
    """
    return Response({'status': 'ready'})


@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(
    responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
    description="Liveness check"
)
def liveness_check(request):
    """
    Liveness check for Kubernetes/Docker.
    Returns 200 if app is running.
    """
    return Response({'status': 'alive'})
