from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Commande, Livraison, Notification, BottleReturn, Subscription, FAQ
from .serializers import CommandeSerializer, LivraisonSerializer, NotificationSerializer, BottleReturnSerializer, SubscriptionSerializer, FAQSerializer

class CommandeViewSet(viewsets.ModelViewSet):
    queryset = Commande.objects.all()  # Requis pour le router DRF
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'client')
        
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return Commande.objects.all()
        elif role == 'agent':
            return Commande.objects.filter(agent=user)
        return Commande.objects.filter(client=user)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign an agent to a command and auto-create Livraison"""
        commande = self.get_object()
        agent_id = request.data.get('agent_id')
        
        if not agent_id:
            return Response(
                {'error': 'agent_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.users.models import CustomUser
            from django.utils import timezone
            from apps.logistics.models import Tournee
            from datetime import date
            agent = CustomUser.objects.get(id=agent_id, role='agent')
            commande.agent = agent
            commande.statut = 'validated'  # Update status when assigned
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
            
            # Auto-create Livraison
            Livraison.objects.create(
                tournee=tournee,
                client_id=commande.client_id,
                commande=commande,
            )

            # Create database notification
            Notification.objects.create(
                user=agent,
                title="Nouvelle commande",
                message=f"La commande #{commande.id} vous a été assignée.",
                type="info"
            )

            # Send real-time notification to the agent
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
            
            serializer = self.get_serializer(commande)
            return Response(serializer.data)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Agent not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class LivraisonViewSet(viewsets.ModelViewSet):
    queryset = Livraison.objects.all()  # Requis pour le router DRF
    serializer_class = LivraisonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'client')
        
        if user.is_superuser or role in ['admin', 'gestionnaire']:
            return Livraison.objects.all()
        elif role == 'agent':
            # Filtrer par le tricycle assigné à l'agent (logique Tournee)
            return Livraison.objects.filter(tournee__agent=user)
        return Livraison.objects.filter(client=user)
    
    @action(detail=True, methods=['post'])
    def submit_proof(self, request, pk=None):
        """Submit delivery proof (photo, signature, GPS)"""
        livraison = self.get_object()
        
        if livraison.preuve_validee:
            return Response(
                {'error': 'Cette livraison est déjà terminée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        # Mark proof as validated
        livraison.preuve_validee = True
        livraison.save()
        
        # Update associated command status
        if livraison.commande:
            livraison.commande.statut = 'delivered'
            livraison.commande.save()
        
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


