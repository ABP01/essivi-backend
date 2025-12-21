from rest_framework import viewsets, permissions
from .models import Commande, Livraison
from .serializers import CommandeSerializer, LivraisonSerializer

class CommandeViewSet(viewsets.ModelViewSet):
    queryset = Commande.objects.all()
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

class LivraisonViewSet(viewsets.ModelViewSet):
    queryset = Livraison.objects.all()
    serializer_class = LivraisonSerializer
    permission_classes = [permissions.IsAuthenticated]
