from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Commande, Livraison, Notification, BottleReturn, Subscription, FAQ
from .serializers import CommandeSerializer, LivraisonSerializer, NotificationSerializer, BottleReturnSerializer, SubscriptionSerializer, FAQSerializer, AgentRatingSerializer
import logging

logger = logging.getLogger('apps.sales')

class CommandeViewSet(viewsets.ModelViewSet):
    queryset = Commande.objects.select_related('agent', 'client').all()
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'client')
        
        # Optimize queries with select_related
        base_queryset = Commande.objects.select_related('agent', 'client')
        
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return base_queryset.all()
        elif role == 'agent':
            return base_queryset.filter(agent=user)
        return base_queryset.filter(client=user)
    
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign an agent to a command and auto-create Livraison. If no agent_id provided, assign nearest available agent."""
        from .services import SalesService
        
        commande = self.get_object()
        agent_id = request.data.get('agent_id')
        
        try:
            result = SalesService.assign_agent_to_command(commande.id, agent_id)
            serializer = self.get_serializer(commande)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'An error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Prevent clients from cancelling a commande that already has an agent assigned."""
        instance = self.get_object()
        user = request.user
        role = getattr(user, 'role', 'client')

        # Admins and gestionnaires can delete any commande
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return super().destroy(request, *args, **kwargs)

        # If a client is trying to delete and an agent is assigned, forbid
        if role == 'client' and instance.agent is not None:
            return Response({'error': 'Commande déjà assignée — annulation impossible.'}, status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)


class LivraisonViewSet(viewsets.ModelViewSet):
    queryset = Livraison.objects.select_related('tournee__agent', 'commande', 'client').all()
    serializer_class = LivraisonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'client')
        
        # Optimize with select_related for related objects
        base_queryset = Livraison.objects.select_related('tournee__agent', 'commande', 'client')
        
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return base_queryset.all()
        elif role == 'agent':
            # Filtrer par le tricycle assigné à l'agent (logique Tournee)
            return base_queryset.filter(tournee__agent=user)
        return base_queryset.filter(client=user)
    
    @action(detail=True, methods=['post'])
    def submit_proof(self, request, pk=None):
        """Submit delivery proof (photo, signature, GPS)"""
        livraison = self.get_object()
        
        # If already validated, return current state instead of error (idempotent)
        if livraison.preuve_validee:
            serializer = self.get_serializer(livraison)
            return Response(serializer.data)
        
        # Update GPS coordinates
        if 'gps_lat' in request.data and 'gps_lng' in request.data:
            livraison.gps_lat = request.data['gps_lat']
            livraison.gps_lng = request.data['gps_lng']
        
        # Update signature (file upload)
        if 'signature' in request.FILES:
            livraison.signature = request.FILES['signature']
        elif 'signature' in request.data:
            livraison.signature = request.data['signature']
        
        # Update photo proof
        if 'photo_preuve' in request.FILES:
            livraison.photo_preuve = request.FILES['photo_preuve']
        
        # Mark delivered, but wait for client validation
        # livraison.preuve_validee = True  <-- Moved to client_validate
        livraison.statut_livraison = 'delivered'
        livraison.save()
        
        # Update associated command status
        if livraison.commande:
            livraison.commande.statut = 'delivered'
            livraison.commande.save()
        
        serializer = self.get_serializer(livraison)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update delivery status (en_route, arriving, etc.)"""
        livraison = self.get_object()
        new_status = request.data.get('statut_livraison')
        
        valid_statuses = ['assigned', 'en_route', 'arriving', 'delivered']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update gps coords if provided by agent
        if 'gps_lat' in request.data:
            try:
                livraison.gps_lat = float(request.data.get('gps_lat'))
            except Exception:
                pass
        if 'gps_lng' in request.data:
            try:
                livraison.gps_lng = float(request.data.get('gps_lng'))
            except Exception:
                pass

        livraison.statut_livraison = new_status
        livraison.save()

        # Create notification for client
        from .models import Notification
        status_messages = {
            'en_route': 'Votre livreur est en route !',
            'arriving': 'Votre livreur arrive bientôt !',
            'delivered': 'Votre commande a été livrée !'
        }

        if new_status in status_messages:
            Notification.objects.create(
                user=livraison.client,
                title='Mise à jour de livraison',
                message=status_messages[new_status],
                type='info'
            )
        
        serializer = self.get_serializer(livraison)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def client_validate(self, request, pk=None):
        """Client validates the delivery after agent submits proof"""
        livraison = self.get_object()
        user = self.request.user
        
        # Only client can validate their own delivery
        if livraison.client != user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if livraison.statut_livraison != 'delivered':
            return Response({'error': 'Delivery not yet completed'}, status=status.HTTP_400_BAD_REQUEST)
        
        livraison.preuve_validee = True
        livraison.save()
        
        # Create notification for agent and admins
        from .models import Notification
        Notification.objects.create(
            user=livraison.commande.agent,
            title='Livraison validée',
            message=f'Le client a validé la livraison #{livraison.id}.',
            type='success'
        )
        
        # Admins
        from apps.users.models import CustomUser
        admins = CustomUser.objects.filter(role__in=['admin', 'gestionnaire'])
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title='Livraison validée',
                message=f'Livraison #{livraison.id} validée par le client.',
                type='info'
            )
        
        serializer = self.get_serializer(livraison)
        return Response(serializer.data)

class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for user notifications"""
    queryset = Notification.objects.all()  # Requis pour le router DRF
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only return notifications for the current user
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        notification.read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user"""
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'message': 'All notifications marked as read'})

class BottleReturnViewSet(viewsets.ModelViewSet):
    """ViewSet for bottle return requests"""
    queryset = BottleReturn.objects.all()  # Requis pour le router DRF
    serializer_class = BottleReturnSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Clients see only their returns, staff see all
        if self.request.user.role in ['admin', 'gestionnaire']:
            return BottleReturn.objects.all()
        return BottleReturn.objects.filter(client=self.request.user)
    
    def perform_create(self, serializer):
        # Automatically set the client to the current user
        serializer.save(client=self.request.user)

class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for client subscriptions"""
    queryset = Subscription.objects.all()  # Requis pour le router DRF
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Clients see only their subscriptions, staff see all
        if self.request.user.role in ['admin', 'gestionnaire']:
            return Subscription.objects.all()
        return Subscription.objects.filter(client=self.request.user)
    
    def perform_create(self, serializer):
        # Automatically set the client to the current user
        serializer.save(client=self.request.user)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a subscription"""
        subscription = self.get_object()
        subscription.status = 'paused'
        subscription.save()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused subscription"""
        subscription = self.get_object()
        subscription.status = 'active'
        subscription.save()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for FAQs (read-only for clients)"""
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = FAQ.objects.filter(is_active=True)

class AgentRatingViewSet(viewsets.ModelViewSet):
    """ViewSet for agent ratings by clients"""
    serializer_class = AgentRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'client')
        
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return AgentRating.objects.all()
        elif role == 'agent':
            return AgentRating.objects.filter(agent=user)
        return AgentRating.objects.filter(client=user)
    
    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


