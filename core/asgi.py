"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

# IMPORTANT: Set DJANGO_SETTINGS_MODULE BEFORE any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI application early to ensure apps are loaded
# This MUST happen before importing anything that depends on Django models
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

# Now it's safe to import modules that depend on Django being initialized
from channels.routing import ProtocolTypeRouter, URLRouter

<<<<<<< HEAD
=======
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_asgi_app = get_asgi_application()

from core.middleware import JWTAuthMiddleware
import apps.sales.routing

>>>>>>> d13d163 (step1)
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            apps.sales.routing.websocket_urlpatterns
        )
    ),
})
