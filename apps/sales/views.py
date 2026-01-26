from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Commande, Livraison, Notification, BottleReturn, Subscription, FAQ
from .serializers import CommandeSerializer, LivraisonSerializer, NotificationSerializer, BottleReturnSerializer, SubscriptionSerializer, FAQSerializer
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
        """Assign an agent to a command and auto-create Livraison"""
        from .services import SalesService
        
        commande = self.get_object()
        agent_id = request.data.get('agent_id')
        
        if not agent_id:
            return Response(
                {'error': 'agent_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        # Mark proof as validated and delivered
        livraison.preuve_validee = True
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


