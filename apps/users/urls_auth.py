from django.urls import path
# Use custom view to set cookies on login
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LogoutView, MeView, ChangePasswordView, CustomTokenObtainPairView

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='auth_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('me/', MeView.as_view(), name='users_me'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
