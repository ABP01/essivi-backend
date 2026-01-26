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
