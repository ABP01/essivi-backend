"""
Health check and monitoring endpoints.
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from django.db import connection
from django.core.cache import cache
import logging
from drf_spectacular.utils import extend_schema

logger = logging.getLogger('apps.dashboard')


# Explicit serializers to help drf-spectacular infer response schemas
from rest_framework import serializers


class ServicesSerializer(serializers.Serializer):
    database = serializers.CharField()
    cache = serializers.CharField()


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    services = ServicesSerializer()


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()


class HealthCheckView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = HealthSerializer

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}, 'services': {'type': 'object'}}}},
        description="Health check endpoint"
    )
    def get(self, request, *args, **kwargs):
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


class ReadinessCheckView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = StatusSerializer

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
        description="Readiness check"
    )
    def get(self, request, *args, **kwargs):
        return Response({'status': 'ready'})


class LivenessCheckView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = StatusSerializer

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
        description="Liveness check"
    )
    def get(self, request, *args, **kwargs):
        return Response({'status': 'alive'})
