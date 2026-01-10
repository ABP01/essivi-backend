from rest_framework import serializers
from .models import Commande, Livraison, Notification, BottleReturn, Subscription, FAQ

class CommandeSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    agent_name = serializers.CharField(source='agent.get_full_name', read_only=True, allow_null=True)
    agent_id = serializers.IntegerField(source='agent.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Commande
        fields = '__all__'

class LivraisonSerializer(serializers.ModelSerializer):
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


