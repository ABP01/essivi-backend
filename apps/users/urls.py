from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import CustomUserViewSet, AgentProfileViewSet, ClientProfileViewSet, RegisterView, LogoutView, MeView

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
]
