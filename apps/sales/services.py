"""
Service layer for Sales app business logic.
Separates complex operations from Views.
"""
import logging
import math
from django.utils import timezone
from django.db import transaction
from apps.users.models import CustomUser, AgentProfile
from apps.logistics.models import Tournee
from .models import Commande, Livraison, Notification

logger = logging.getLogger('apps.sales')


class SalesService:
    """Service class for Sales-related business logic."""

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula (in km)"""
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    @staticmethod
    def find_nearest_agent(client_lat, client_lng):
        """Find the nearest available agent to the client location"""
        agents = AgentProfile.objects.filter(
            user__role='agent',
            latitude__isnull=False,
            longitude__isnull=False,
            is_online=True
        ).select_related('user')
        
        nearest_agent = None
        min_distance = float('inf')
        
        for agent_profile in agents:
            distance = SalesService.calculate_distance(
                client_lat, client_lng,
                agent_profile.latitude, agent_profile.longitude
            )
            if distance < min_distance:
                min_distance = distance
                nearest_agent = agent_profile.user
        
        return nearest_agent, min_distance

    @staticmethod
    @transaction.atomic
    def assign_agent_to_command(commande_id: int, agent_id: int = None) -> dict:
        """
        Assign an agent to a command and auto-create Livraison and Tournee.
        
        Args:
            commande_id: ID of the command to assign
            agent_id: ID of the agent to assign
            
        Returns:
            dict with success status and optional error message
            
        Raises:
            ValueError: If agent or command not found or agent is not valid
        """
        try:
            commande = Commande.objects.select_for_update().get(id=commande_id)
        except Commande.DoesNotExist:
            raise ValueError(f'Command {commande_id} not found')
        
        if agent_id:
            try:
                agent = CustomUser.objects.get(id=agent_id, role='agent')
            except CustomUser.DoesNotExist:
                raise ValueError(f'Agent {agent_id} not found or user is not an agent')
        else:
            # Find nearest agent
            if not hasattr(commande.client, 'client_profile') or not commande.client.client_profile.gps_lat or not commande.client.client_profile.gps_lng:
                raise ValueError('Client location not available for automatic assignment')
            
            agent, distance = SalesService.find_nearest_agent(
                commande.client.client_profile.gps_lat,
                commande.client.client_profile.gps_lng
            )
            if not agent:
                raise ValueError('No available agents found')
            if distance > 10:  # Max 10km
                raise ValueError(f'No agents within 10km (nearest is {distance:.1f}km away)')
        
        # Update command
        commande.agent = agent
        commande.statut = 'validated'
        commande.save()
        
        # Auto-create a Tournee for today if it doesn't exist
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        tournee, created = Tournee.objects.get_or_create(
            agent=agent,
            date_debut__gte=today_start,
            date_debut__lte=today_end,
            defaults={
                'date_debut': timezone.now(),
                'stock_initial': 0
            }
        )
        
        # Auto-create or update Livraison
        livraison, created = Livraison.objects.get_or_create(
            commande=commande,
            defaults={
                'tournee': tournee,
                'client_id': commande.client_id,
            }
        )
        
        # If livraison already existed, update the tournee (in case of reassignment)
        if not created:
            livraison.tournee = tournee
            livraison.save()

        # Create database notification
        Notification.objects.create(
            user=agent,
            title="Nouvelle commande",
            message=f"La commande #{commande.id} vous a été assignée.",
            type="info"
        )

        # Send real-time notification via WebSocket
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{agent.id}",
                    {
                        "type": "send_notification",
                        "message": f"Nouvelle commande assignée : {commande.id}"
                    }
                )
        except Exception as e:
            # Log but don't fail the entire operation if WebSocket fails
            logger.error(f"WebSocket notification failed: {e}", exc_info=True)
        
        return {
            'success': True,
            'commande_id': commande.id,
            'agent_id': agent.id,
            'livraison_id': livraison.id,
            'tournee_id': tournee.id,
        }
