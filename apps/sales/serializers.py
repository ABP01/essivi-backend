from rest_framework import serializers
from .models import Commande, Livraison, Notification, BottleReturn, Subscription, FAQ, AgentRating, Product, OrderItem
from drf_spectacular.utils import extend_schema_field

class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    @extend_schema_field(serializers.CharField())
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_category = serializers.CharField(source='product.category', read_only=True)
    product_unit = serializers.CharField(source='product.unit', read_only=True)
    product_quantity_per_unit = serializers.IntegerField(source='product.quantity_per_unit', read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'

class CommandeSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.username', read_only=True)
    client_phone = serializers.CharField(source='client.phone_number', read_only=True)
    agent_name = serializers.SerializerMethodField()
    agent_phone = serializers.SerializerMethodField()
    agent_id = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    items_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of items to create with the order"
    )
    
    def get_agent_name(self, obj):
        return obj.agent.username if obj.agent else None
    
    def get_agent_phone(self, obj):
        return obj.agent.phone_number if obj.agent else None
    
    def get_agent_id(self, obj):
        return obj.agent.id if obj.agent else None
    
    def create(self, validated_data):
        items_data = validated_data.pop('items_data', [])
        commande = super().create(validated_data)
        
        # Create order items
        for item_data in items_data:
            product_id = item_data.get('product')
            quantity = item_data.get('quantity', 1)
            try:
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(
                    commande=commande,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price
                )
            except Product.DoesNotExist:
                pass  # Skip invalid products
        
        # Update total amount
        commande.update_total_amount()
        return commande
    
    class Meta:
        model = Commande
        fields = '__all__'
        read_only_fields = ['client', 'agent', 'statut', 'montant', 'created_at', 'updated_at']

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

class AgentRatingSerializer(serializers.ModelSerializer):
    """Serializer for agent ratings"""
    client_name = serializers.CharField(source='client.username', read_only=True)
    agent_name = serializers.CharField(source='agent.username', read_only=True)
    commande_id = serializers.IntegerField(source='commande.id', read_only=True)
    
    class Meta:
        model = AgentRating
        fields = ['id', 'client', 'client_name', 'agent', 'agent_name', 'commande', 'commande_id', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


