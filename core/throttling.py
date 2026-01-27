"""
Custom throttle classes for rate limiting.
"""
from rest_framework.throttling import UserRateThrottle


class LoginRateThrottle(UserRateThrottle):
    """
    Limite les tentatives de login à 5 par minute pour éviter le brute force.
    """
    rate = '5/minute'
    scope = 'login'


from rest_framework.throttling import AnonRateThrottle


class HealthExemptAnonRateThrottle(AnonRateThrottle):
    """
    Anonymous throttle that exempts health check endpoints and whitelisted IPs.
    """
    def allow_request(self, request, view):
        try:
            # Exempt health endpoint from throttling to avoid infra probes causing 429
            if request.path.startswith('/health') or request.path.startswith('/health/'):
                return True
        except Exception:
            pass
        return super().allow_request(request, view)
