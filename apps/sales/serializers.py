from rest_framework import serializers
from .models import Commande, Livraison

class CommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = '__all__'

class LivraisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Livraison
        fields = '__all__'
