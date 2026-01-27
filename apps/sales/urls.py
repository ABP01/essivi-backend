from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommandeViewSet, LivraisonViewSet, NotificationViewSet, BottleReturnViewSet, SubscriptionViewSet, FAQViewSet, AgentRatingViewSet

router = DefaultRouter()
router.register(r'commandes', CommandeViewSet)
router.register(r'livraisons', LivraisonViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'bottle-returns', BottleReturnViewSet, basename='bottle-return')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'agent-ratings', AgentRatingViewSet, basename='agent-rating')

urlpatterns = [
    path('', include(router.urls)),
]
