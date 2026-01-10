from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser, AgentProfile, ClientProfile
from .serializers import CustomUserSerializer, AgentProfileSerializer, ClientProfileSerializer, RegisterSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

from drf_spectacular.utils import extend_schema

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
        
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return AgentProfile.objects.all()
        # Clients peuvent voir les profils des agents pour les commandes en cours
        return AgentProfile.objects.all() # On garde permissif pour l'instant car l'UI en a besoin

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

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)

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

class UserPreferencesView(APIView):
    """API endpoint for getting and updating user preferences"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .serializers import UserPreferencesSerializer
        from .models import UserPreferences
        
        # Get or create preferences for the user
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data)

    def put(self, request):
        from .serializers import UserPreferencesSerializer
        from .models import UserPreferences
        
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

