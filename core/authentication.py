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

        users_service = Users(client)

        try:
            # Verify the JWT token not directly supported by server-side SDK for verification 
            # in the same way as client, but we can usually validate it by making a request 
            # acting as the user or validating usage.
            # However, standard practice with Appwrite backend to backend is trusting the 
            # JWT claim if we were decoding it, OR using the server SDK to fetch user info.
            
            # Since Appwrite Server SDK doesn't have a direct "validate_jwt" method that returns 
            # the user object from a JWT string without decoding it yourself or using logic,
            # we might need to assume the mobile sends the USER_ID and SESSION_ID/JWT.
            
            # BUT, the most secure way without implementing local JWT decoding (strategies 
            # depend on algorithm) is to trust that if we can perform an action, it's valid. 
            
            # Actually, standard Appwrite pattern for Backend is:
            # 1. Received JWT from Client.
            # 2. Client uses Account.createJWT().
            # 3. Backend verifies this.
            
            # Wait, Appwrite SDKs for different languages behave differently.
            # In Python SDK, simplified approach:
            
            # Ideally we'd use a library to decode the JWT and check the signature if we verify locally.
            # Appwrite uses HS256 (default) or RS256. 
            # For simplicity & security, we should really verify the token against Appwrite API 
            # if possible, but Appwrite API 'get account' usually requires session cookies.
            
            # ALTERNATIVE: JWT verification logic.
            # Since we don't have the Appwrite signing secret easily exposed without scraping it 
            # or it being the API Key (it's not), we usually need to set the JWT as the session 
            # on the client? No, Server SDK uses API Key.
            
            # Let's check Appwrite docs logic:
            # "The Client SDK allows you to create a JWT... You can then send this JWT to your 
            # backend... Your backend can then use this JWT to authenticate with Appwrite 
            # to verify the user's identity."
            
            # How?
            # client.set_jwt(token)
            # account.get() -> returns user if valid.
            
            # Let's try that specific flow which is standard for Appwrite <-> Backend.
            
            client_for_verification = Client()
            client_for_verification.set_endpoint(os.getenv('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1'))
            client_for_verification.set_project(os.getenv('APPWRITE_PROJECT_ID'))
            client_for_verification.set_jwt(token) # Set the user's JWT
            
            from appwrite.services.account import Account
            account = Account(client_for_verification)
            appwrite_user = account.get()
            
            # If successful, we have the user data.
            email = appwrite_user.get('email')
            phone = appwrite_user.get('phone')
            user_id = appwrite_user.get('$id')
            
            if not email and not phone:
                 raise exceptions.AuthenticationFailed('Appwrite user must have email or phone')

            # Find or Create User in Django
            # Priority: ID Match -> Email Match -> Phone Match
            
            user = None
            
            # Try to find by Appwrite ID (stored in username or separate field?)
            # Storing in username is risky if we want human readable usernames.
            # But let's check existing logic.
            
            # Strategy:
            # 1. Try fetching by email (if exists)
            # 2. Try fetching by phone (if exists)
            # 3. Create if not exists
            
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    pass
            
            if not user and phone:
                # Assuming 'phone_number' field exists on your custom user model or profile
                # Let's check the models file next time, but for now we'll rely on existing fields.
                # Standard User model might not have phone.
                pass

            if not user:
                # Create user
                # We use the Appwrite ID as the username to ensure uniqueness map
                username = user_id
                
                # Check if username exists (rare collision case with old data)
                if User.objects.filter(username=username).exists():
                     user = User.objects.get(username=username)
                else:
                    user = User.objects.create_user(
                        username=username,
                        email=email if email else '',
                        password=None # Unusable password
                    )
                    user.save()
            
            return (user, None)

        except Exception as e:
            # Log the error for debug
            print(f"Appwrite Auth Error: {str(e)}")
            raise exceptions.AuthenticationFailed(f'Invalid Authentication: {str(e)}')
