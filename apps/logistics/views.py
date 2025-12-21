from rest_framework import viewsets, permissions
from .models import Tricycle, Tournee
from .serializers import TricycleSerializer, TourneeSerializer

class TricycleViewSet(viewsets.ModelViewSet):
    queryset = Tricycle.objects.all()
    serializer_class = TricycleSerializer
    permission_classes = [permissions.IsAuthenticated]

class TourneeViewSet(viewsets.ModelViewSet):
    queryset = Tournee.objects.all()
    serializer_class = TourneeSerializer
    permission_classes = [permissions.IsAuthenticated]
