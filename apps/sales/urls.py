from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommandeViewSet, LivraisonViewSet

router = DefaultRouter()
router.register(r'commandes', CommandeViewSet)
router.register(r'livraisons', LivraisonViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
