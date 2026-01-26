from rest_framework import serializers
from .models import Commande, Livraison, Notification, BottleReturn, Subscription, FAQ
from drf_spectacular.utils import extend_schema_field

class CommandeSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.username', read_only=True)
    client_phone = serializers.CharField(source='client.phone_number', read_only=True)
    agent_name = serializers.CharField(source='agent.username', read_only=True, allow_null=True)
    agent_phone = serializers.CharField(source='agent.phone_number', read_only=True, allow_null=True)
    agent_id = serializers.IntegerField(source='agent.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Commande
        fields = '__all__'

class LivraisonSerializer(serializers.ModelSerializer):
    client_phone = serializers.CharField(source='client.phone_number', read_only=True)
    client_name = serializers.SerializerMethodField()
    agent_phone = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    
    @extend_schema_field(serializers.CharField())
    def get_client_name(self, obj):
        # Try to get from linked commande first, fallback to user
        if obj.commande and obj.commande.client:
            return obj.commande.client.username
        return obj.client.username if obj.client else None
    
    @extend_schema_field(serializers.CharField())
    def get_agent_phone(self, obj):
        # Get agent phone from tournee
        if obj.tournee and obj.tournee.agent:
            return obj.tournee.agent.phone_number
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_agent_name(self, obj):
        # Get agent name from tournee
        if obj.tournee and obj.tournee.agent:
            return obj.tournee.agent.username
        # Or from linked commande
        elif obj.commande and obj.commande.agent:
            return obj.commande.agent.username
        return None
    
    @extend_schema_field(serializers.FloatField())
    def get_amount(self, obj):
        # Get amount from linked commande
        if obj.commande:
            return float(obj.commande.montant)
        return 0.0
    
    @extend_schema_field(serializers.CharField())
    def get_address(self, obj):
        # Try to get from client profile or commande
        if obj.client and hasattr(obj.client, 'client_profile'):
            profile = obj.client.client_profile
            if profile.formatted_address:
                return profile.formatted_address
            elif profile.adresse:
                return profile.adresse
        return ''
    
    class Meta:
        model = Livraison
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications"""
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'read', 'created_at']
        read_only_fields = ['id', 'created_at']

class BottleReturnSerializer(serializers.ModelSerializer):
    """Serializer for bottle return requests"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    
    class Meta:
        model = BottleReturn
        fields = ['id', 'client', 'client_name', 'bottle_count', 'credit_amount', 'status', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'credit_amount', 'created_at', 'updated_at']

class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for client subscriptions"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    
    class Meta:
        model = Subscription
        fields = ['id', 'client', 'client_name', 'plan', 'bottle_size', 'quantity', 'preferred_day', 'time_slot', 'status', 'next_delivery', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQs"""
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'order', 'is_active']
        read_only_fields = ['id']


