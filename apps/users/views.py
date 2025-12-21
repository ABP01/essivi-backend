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
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    # Allow read-only (GET) access to anonymous users for development UI convenience;
    # require authentication for mutating actions.
    def get_permissions(self):
        if self.request and self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

class AgentProfileViewSet(viewsets.ModelViewSet):
    queryset = AgentProfile.objects.all()
    serializer_class = AgentProfileSerializer
    # Allow read-only (GET) access to anonymous users for development UI convenience;
    # require authentication for mutating actions.
    def get_permissions(self):
        if self.request and self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    def get_permissions(self):
        if self.request and self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
