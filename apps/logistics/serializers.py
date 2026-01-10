from rest_framework import serializers
from .models import Tricycle, Tournee
from .models import Tricycle, Tournee, LocationHistory
from apps.users.models import AgentProfile

class TricycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tricycle
        fields = '__all__'

class TourneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournee
        fields = '__all__'

class LocationHistorySerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des positions"""
    agent_name = serializers.CharField(source='agent.user.username', read_only=True)
    
    class Meta:
        model = LocationHistory
        fields = ['id', 'agent', 'agent_name', 'latitude', 'longitude', 
                  'timestamp', 'accuracy', 'speed', 'heading']
        read_only_fields = ['timestamp']

class AgentLocationSerializer(serializers.Serializer):
    """Serializer pour mettre à jour la position d'un agent"""
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    accuracy = serializers.FloatField(required=False, allow_null=True)
    speed = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.FloatField(required=False, allow_null=True)

class AgentPositionSerializer(serializers.ModelSerializer):
    """Serializer pour afficher la position actuelle d'un agent"""
    agent_id = serializers.IntegerField(source='id', read_only=True)
    agent_name = serializers.CharField(source='user.username', read_only=True)
    agent_phone = serializers.CharField(source='user.phone_number', read_only=True)
    current_deliveries = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentProfile
        fields = ['agent_id', 'agent_name', 'agent_phone', 'latitude', 'longitude',
                  'is_online', 'last_location_update', 'current_speed', 'heading',
                  'current_deliveries']
    
    def get_current_deliveries(self, obj):
        """Compte le nombre de livraisons en cours pour cet agent"""
        from apps.sales.models import Livraison
        return Livraison.objects.filter(
            agent=obj.user,
            preuve_validee=False
        ).count()
