import os
from appwrite.client import Client
from appwrite.services.users import Users
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class AppwriteAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for Appwrite.
    Verifies the Appwrite JWT token and gets/creates the corresponding Django user.
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
            
        try:
            # Expecting 'Bearer <token>'
            auth_type, token = auth_header.split(' ')
            if auth_type.lower() != 'bearer':
                return None
        except ValueError:
            return None

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        # Initialize Appwrite Client
        client = Client()
        client.set_endpoint(os.getenv('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1'))
        client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        client.set_key(os.getenv('APPWRITE_API_KEY'))

        try:
            # Verify the JWT by setting it as the client's JWT and fetching the account
            client_for_verification = Client()
            client_for_verification.set_endpoint(os.getenv('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1'))
            client_for_verification.set_project(os.getenv('APPWRITE_PROJECT_ID'))
            client_for_verification.set_jwt(token)
            
            from appwrite.services.account import Account
            account = Account(client_for_verification)
            appwrite_user = account.get()
            
            # Extract user info
            email = appwrite_user.get('email')
            phone = appwrite_user.get('phone')
            user_id = appwrite_user.get('$id')
            name = appwrite_user.get('name')
            
            if not email and not phone:
                 raise exceptions.AuthenticationFailed('Appwrite user must have email or phone')

            # Find or Create User in Django
            user = None
            
            # 1. Try to find by Appwrite ID (stored in username)
            try:
                user = User.objects.get(username=user_id)
            except User.DoesNotExist:
                pass
            
            # 2. If not found, try to find by phone (if available)
            if not user and phone:
                # Assuming 'phone' is unique. If you have a custom user model with phone field:
                # user = User.objects.filter(phone=phone).first()
                # For basic User model, we might not have phone field, so we skip or assume username=phone?
                # Let's stick to username=user_id for reliable mapping.
                pass

            # 3. Create if not exists
            if not user:
                # Create user with Appwrite ID as username
                user = User.objects.create_user(
                    username=user_id,
                    email=email if email else '',
                    first_name=name if name else '',
                    password=None # Unusable password
                )
                # If we have a custom user model with phone, set it here
                if phone and hasattr(user, 'phone'):
                    user.phone = phone
                user.save()
                
                # Assign default role if applicable (handled by signals or default on model)
                
                # Check for Profile and create if missing
                try:
                    from apps.users.models import ClientProfile
                    if not hasattr(user, 'client_profile'):
                        ClientProfile.objects.create(user=user, nom_point_vente=f"Shop-{user.username}")
                except Exception as e:
                    print(f"Error creating profile: {e}")
                    pass
            
            return (user, None)

        except Exception as e:
            # Log the error for debug
            print(f"Appwrite Auth Error: {str(e)}")
            raise exceptions.AuthenticationFailed(f'Invalid Authentication: {str(e)}')
