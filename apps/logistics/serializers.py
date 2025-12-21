from rest_framework import serializers
from .models import Tricycle, Tournee

class TricycleSerializer(serializers.ModelSerializer):
    def validate_immatriculation(self, value):
        import re
        # expect format: two letters, dash, two digits, dash, two digits -> AB-12-34
        if not re.match(r'^[A-Z]{2}-\d{2}-\d{2}$', value):
            raise serializers.ValidationError('Immatriculation invalide. Format attendu : AA-12-34')
        return value
    class Meta:
        model = Tricycle
        fields = '__all__'

class TourneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournee
        fields = '__all__'
