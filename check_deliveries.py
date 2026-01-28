#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.sales.models import Livraison

def check_deliveries():
    try:
        livraisons = Livraison.objects.all()
        print(f"Total livraisons: {livraisons.count()}")

        coords = livraisons.filter(gps_lat__isnull=False, gps_lng__isnull=False)
        print(f"Livraisons with coordinates: {coords.count()}")

        print("\nDelivery details (first 5):")
        for livraison in livraisons[:5]:
            print(f"Livraison {livraison.id}: lat={livraison.gps_lat}, lng={livraison.gps_lng}, status={livraison.statut_livraison}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_deliveries()