from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TricycleViewSet, TourneeViewSet

router = DefaultRouter()
router.register(r'tricycles', TricycleViewSet)
router.register(r'tournees', TourneeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
