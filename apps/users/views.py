from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, AgentProfile, ClientProfile, PasswordResetToken
from .serializers import CustomUserSerializer, AgentProfileSerializer, ClientProfileSerializer, RegisterSerializer, UserPreferencesSerializer, MeSerializer, CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        response_data = {
            'user': CustomUserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

from drf_spectacular.utils import extend_schema

from rest_framework import serializers as drf_serializers

# Response serializer for token endpoints combining tokens + user
class TokenUserSerializer(drf_serializers.Serializer):
    access = drf_serializers.CharField()
    refresh = drf_serializers.CharField()
    user = CustomUserSerializer()

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={205: None},
        description="Blacklist the refresh token to logout user."
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()  # Requis pour le router DRF
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'client')
        
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return CustomUser.objects.all()
        # Un utilisateur ne peut voir que son propre compte via ce ViewSet
        return CustomUser.objects.filter(id=user.id)

class AgentProfileViewSet(viewsets.ModelViewSet):
    queryset = AgentProfile.objects.all()  # Requis pour le router DRF
    serializer_class = AgentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'client')
        
        # Admins and gestionnaires can view all agent profiles
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return AgentProfile.objects.all()
        # Agents can see their own profile
        if role == 'agent':
            return AgentProfile.objects.filter(user=user)
        # Clients and other roles should not see agent list for security
        return AgentProfile.objects.none()

class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.all()  # Requis pour le router DRF
    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'client')
        
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return ClientProfile.objects.all()
        elif role == 'client':
            return ClientProfile.objects.filter(user=user)
        return ClientProfile.objects.none() # Agents ne voient pas tous les profils clients par défaut


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=MeSerializer,
        responses={200: MeSerializer},
        description="Get current user profile"
    )
    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=CustomUserSerializer,
        responses={200: CustomUserSerializer},
        description="Update current user profile"
    )
    def patch(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    """API endpoint for changing user password"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: None},
        description="Change user password"
    )
    def post(self, request):
        from .serializers import ChangePasswordSerializer
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    """API endpoint for requesting password reset"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=None,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        description="Request password reset"
    )
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not for security
            return Response({'message': 'If the email exists, a reset link has been sent.'}, status=status.HTTP_200_OK)

        # Generate token
        token = get_random_string(64)
        reset_token = PasswordResetToken.objects.create(user=user, token=token)

        # Send email
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = 'Réinitialisation de votre mot de passe Essivi'
        message = f"""
        Bonjour {user.first_name or user.username},

        Vous avez demandé la réinitialisation de votre mot de passe pour l'application Essivi.

        Cliquez sur le lien suivant pour réinitialiser votre mot de passe :
        {reset_url}

        Ce lien expirera dans 24 heures.

        Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

        Cordialement,
        L'équipe Essivi
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send reset email: {e}")

        return Response({'message': 'If the email exists, a reset link has been sent.'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    """API endpoint for confirming password reset with token"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=None,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        description="Confirm password reset"
    )
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response({'error': 'Token and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reset_token = PasswordResetToken.objects.get(token=token, used=False)
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        if reset_token.is_expired():
            return Response({'error': 'Token has expired'}, status=status.HTTP_400_BAD_REQUEST)

        # Update password
        user = reset_token.user
        user.set_password(new_password)
        user.save()

        # Mark token as used
        reset_token.used = True
        reset_token.save()

        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)

class UserPreferencesView(APIView):
    """API endpoint for getting and updating user preferences"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: UserPreferencesSerializer},
        description="Get user preferences"
    )
    def get(self, request):
        from .serializers import UserPreferencesSerializer
        from .models import UserPreferences
        
        # Get or create preferences for the user
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data)

    @extend_schema(
        request=UserPreferencesSerializer,
        responses={200: UserPreferencesSerializer},
        description="Update user preferences"
    )
    def put(self, request):
        from .serializers import UserPreferencesSerializer
        from .models import UserPreferences
        
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppwriteLoginView(APIView):
    """
    Exchanges an Appwrite JWT for a Django SimpleJWT pair.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=None,
        responses={200: TokenUserSerializer},
        description="Login with Appwrite JWT"
    )
    def post(self, request):
        jwt_token = request.data.get('jwt')
        if not jwt_token:
            return Response({'error': 'JWT is required'}, status=status.HTTP_400_BAD_REQUEST)

        from core.authentication import AppwriteAuthentication
        auth = AppwriteAuthentication()
        try:
            user, _ = auth.authenticate_credentials(jwt_token)
        except Exception as e:
            return Response({'error': f'Authentication failed: {str(e)}'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user:
             return Response({'error': 'User not found or created'}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate SimpleJWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': CustomUserSerializer(user).data
        })


from core.throttling import LoginRateThrottle


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that sets HttpOnly cookies for access and refresh tokens
    in addition to returning the tokens in the JSON body. This helps server-side
    middleware on the frontend domain read auth state reliably.
    """
    serializer_class = CustomTokenObtainPairSerializer

    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        access = data.get('access')
        refresh = data.get('refresh')

        # Build response with tokens (same shape as original view)
        response = Response({
            'access': access,
            'refresh': refresh,
        })

        # Set cookies so Next.js middleware can read them on incoming requests
        try:
            secure_flag = not settings.DEBUG
            # Access token short-lived (8 hours)
            response.set_cookie(
                'access_token',
                access,
                max_age=8 * 60 * 60,
                path='/',
                secure=secure_flag,
                httponly=True,
                samesite='None' if secure_flag else 'Lax'
            )
            # Refresh token longer (7 days)
            response.set_cookie(
                'refresh_token',
                refresh,
                max_age=7 * 24 * 60 * 60,
                path='/',
                secure=secure_flag,
                httponly=True,
                samesite='None' if secure_flag else 'Lax'
            )
        except Exception as e:
            # If cookie setting fails for any reason, continue returning tokens
            print(f"Failed to set auth cookies: {e}")

        return response

