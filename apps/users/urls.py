from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import CustomUserViewSet, AgentProfileViewSet, ClientProfileViewSet, RegisterView, LogoutView, MeView, ChangePasswordView, UserPreferencesView, PasswordResetRequestView, PasswordResetConfirmView

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'agents', AgentProfileViewSet)
router.register(r'clients', ClientProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('me/', MeView.as_view(), name='users_me'),
    path('auth/signup/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='auth_login'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('preferences/', UserPreferencesView.as_view(), name='user_preferences'),
]

