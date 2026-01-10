from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (TricycleViewSet, TourneeViewSet, AgentLocationView,
                    AgentLocationsView, NearestAgentsView, TestAgentLocationView)

router = DefaultRouter()
router.register(r'tricycles', TricycleViewSet)
router.register(r'tournees', TourneeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Endpoints de géolocalisation
    path('agents/<int:agent_id>/update_location/', AgentLocationView.as_view(), name='agent-update-location'),
    path('agents/locations/', AgentLocationsView.as_view(), name='agent-locations'),
    path('agents/nearest/', NearestAgentsView.as_view(), name='nearest-agents'),
    path('agents/test_location/', TestAgentLocationView.as_view(), name='test-agent-location'),
]
