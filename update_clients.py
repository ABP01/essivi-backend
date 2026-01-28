#!/usr/bin/env python
import os
import sys
import django
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.users.models import ClientProfile

def update_clients():
    clients = ClientProfile.objects.all()
    base_lat, base_lng = 6.1319, 1.2228  # Lomé, Togo

    print(f"Updating {clients.count()} clients with coordinates...")

    for i, client in enumerate(clients):
        # Skip if already has coordinates
        if client.gps_lat is not None and client.gps_lng is not None:
            print(f"Client {client.user.username} already has coordinates")
            continue

        # Add some random variation around Lomé
        lat = base_lat + random.uniform(-0.03, 0.03)
        lng = base_lng + random.uniform(-0.03, 0.03)

        client.gps_lat = lat
        client.gps_lng = lng
        client.save()

        print(f"Updated client {client.user.username}: lat={lat:.4f}, lng={lng:.4f}")

    print("Client update completed!")

if __name__ == '__main__':
    update_clients()