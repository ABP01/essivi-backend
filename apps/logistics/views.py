from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Tricycle, Tournee, LocationHistory
from .serializers import (TricycleSerializer, TourneeSerializer, 
                          LocationHistorySerializer, AgentLocationSerializer,
                          AgentPositionSerializer)
from apps.users.models import AgentProfile
from .utils import find_nearest_agents

class TricycleViewSet(viewsets.ModelViewSet):
    queryset = Tricycle.objects.all()
    serializer_class = TricycleSerializer
    permission_classes = [permissions.IsAuthenticated]

class TourneeViewSet(viewsets.ModelViewSet):
    queryset = Tournee.objects.all()
    serializer_class = TourneeSerializer
    permission_classes = [permissions.IsAuthenticated]

class AgentLocationView(APIView):
    """
    Vue pour mettre à jour la position d'un agent
    POST /api/logistics/agents/{agent_id}/update_location/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, agent_id):
        try:
            agent_profile = AgentProfile.objects.get(id=agent_id)
        except AgentProfile.DoesNotExist:
            return Response(
                {'error': 'Agent non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que l'utilisateur est bien cet agent ou un admin
        if request.user != agent_profile.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AgentLocationSerializer(data=request.data)
        if serializer.is_valid():
            # Mettre à jour la position de l'agent
            agent_profile.latitude = serializer.validated_data['latitude']
            agent_profile.longitude = serializer.validated_data['longitude']
            agent_profile.current_speed = serializer.validated_data.get('speed')
            agent_profile.heading = serializer.validated_data.get('heading')
            agent_profile.last_location_update = timezone.now()
            agent_profile.is_online = True
            agent_profile.save()
            
            # Sauvegarder dans l'historique
            LocationHistory.objects.create(
                agent=agent_profile,
                latitude=serializer.validated_data['latitude'],
                longitude=serializer.validated_data['longitude'],
                accuracy=serializer.validated_data.get('accuracy'),
                speed=serializer.validated_data.get('speed'),
                heading=serializer.validated_data.get('heading')
            )
            
            return Response({
                'success': True,
                'message': 'Position mise à jour avec succès'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AgentLocationsView(APIView):
    """
    Vue pour obtenir les positions de tous les agents
    GET /api/logistics/agents/locations/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Filtrer les agents en ligne avec position
        agents = AgentProfile.objects.filter(
            is_online=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('user')
        
        serializer = AgentPositionSerializer(agents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NearestAgentsView(APIView):
    """
    Vue pour trouver les agents les plus proches d'une position
    POST /api/logistics/agents/nearest/
    Body: {"latitude": 6.1319, "longitude": 1.2223, "max_agents": 5}
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        max_agents = request.data.get('max_agents', 5)
        
        if not latitude or not longitude:
            return Response(
                {'error': 'Latitude et longitude requises'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtenir tous les agents en ligne
        agents = AgentProfile.objects.filter(is_online=True).select_related('user')
        
        # Trouver les plus proches
        nearest = find_nearest_agents(latitude, longitude, agents, max_agents)
        
        # Formater la réponse
        result = []
        for agent, distance in nearest:
            result.append({
                'agent_id': agent.id,
                'agent_name': agent.user.username,
                'agent_phone': agent.user.phone_number,
                'latitude': agent.latitude,
                'longitude': agent.longitude,
                'distance_km': round(distance, 2),
                'current_deliveries': Livraison.objects.filter(tournee__agent=agent.user, preuve_validee=False).count()
            })
        
        return Response(result, status=status.HTTP_200_OK)

class TestAgentLocationView(APIView):
    """
    Vue de test pour faciliter le débogage de la géolocalisation
    GET /api/logistics/agents/test_location/
    Returns count of online agents and their basic info
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Stats générales
        total_agents = AgentProfile.objects.count()
        online_agents = AgentProfile.objects.filter(is_online=True).count()
        agents_with_location = AgentProfile.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).count()
        agents_trackable = AgentProfile.objects.filter(
            is_online=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).count()
        
        # Détails des agents traçables
        trackable_agents = AgentProfile.objects.filter(
            is_online=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('user')
        
        agents_list = [{
            'id': agent.id,
            'username': agent.user.username,
            'latitude': agent.latitude,
            'longitude': agent.longitude,
            'last_update': agent.last_location_update,
            'speed': agent.current_speed,
        } for agent in trackable_agents]
        
        return Response({
            'stats': {
                'total_agents': total_agents,
                'online_agents': online_agents,
                'agents_with_location': agents_with_location,
                'agents_trackable': agents_trackable,
            },
            'trackable_agents': agents_list,
            'message': f'{agents_trackable} agents are currently trackable'
        }, status=status.HTTP_200_OK)
