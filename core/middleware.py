from django.db import close_old_connections
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
from channels.db import database_sync_to_async

class JWTAuthMiddleware:
    """
    Custom middleware that takes token from query string and authenticates user
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")

        if token:
            token = token[0]
            scope["user"] = await self.get_user(token)
        else:
            from django.contrib.auth.models import AnonymousUser
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        try:
            # Get User model inside the method to avoid early loading
            User = get_user_model()
            
            # Decode the token
            UntypedToken(token)
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get("user_id")
            
            # Close old database connections to prevent errors
            close_old_connections()
            
            return User.objects.get(id=user_id)
        except (InvalidToken, TokenError, Exception):
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()

