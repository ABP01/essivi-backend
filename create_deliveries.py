#!/usr/bin/env python
import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.sales.models import Livraison, Commande
from apps.users.models import ClientProfile

def create_test_deliveries():
    clients = ClientProfile.objects.all()
    base_lat, base_lng = 6.1319, 1.2228  # Lomé, Togo

    print(f"Creating test deliveries for {clients.count()} clients...")

    for client in clients:
        # Create 2-5 deliveries per client
        num_deliveries = random.randint(2, 5)

        for i in range(num_deliveries):
            # Create a fake delivery with coordinates near the client
            lat = client.gps_lat + random.uniform(-0.005, 0.005) if client.gps_lat else base_lat + random.uniform(-0.02, 0.02)
            lng = client.gps_lng + random.uniform(-0.005, 0.005) if client.gps_lng else base_lng + random.uniform(-0.02, 0.02)

            # Create delivery
            livraison = Livraison.objects.create(
                client=client.user,
                gps_lat=lat,
                gps_lng=lng,
                statut_livraison='delivered',
                timestamp=datetime.now() - timedelta(days=random.randint(0, 30))
            )

            print(f"Created delivery {livraison.id} for client {client.nom_point_vente}: lat={lat:.4f}, lng={lng:.4f}")

    print("Test deliveries creation completed!")

if __name__ == '__main__':
    create_test_deliveries()