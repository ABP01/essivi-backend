#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.users.models import ClientProfile

def check_clients():
    try:
        clients = ClientProfile.objects.all()
        print(f"Total clients: {clients.count()}")

        coords = clients.filter(gps_lat__isnull=False, gps_lng__isnull=False)
        print(f"Clients with coordinates: {coords.count()}")

        print("\nClient details (first 3):")
        for client in clients[:3]:
            print(f"Client {client.user.username}: lat={client.gps_lat}, lng={client.gps_lng}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_clients()