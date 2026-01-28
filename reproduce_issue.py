import os
import django
import sys
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework.exceptions import ValidationError
from apps.users.models import CustomUser
from apps.sales.models import Product, Commande, OrderItem
from apps.sales.serializers import CommandeSerializer
from django.utils import timezone

def run_debug():
    print("--- Starting Debug ---")
    
    # 1. Fetch User
    try:
        # Try finding the user from the logs (ID 7)
        client = CustomUser.objects.filter(id=7).first()
        if not client:
            print("User ID 7 not found, using first available client/user.")
            client = CustomUser.objects.first()
            
        if not client:
            print("CRITICAL: No users found in DB.")
            return
            
        print(f"Using Client: {client.username} (ID: {client.id})")
    except Exception as e:
        print(f"Error fetching user: {e}")
        return

    # 2. Fetch Product
    try:
        # Try finding product from logs (ID 7)
        product = Product.objects.filter(id=7).first()
        if not product:
            print("Product ID 7 not found, using first available product.")
            product = Product.objects.first()
            
        if not product:
            print("CRITICAL: No products found in DB.")
            return

        print(f"Using Product: {product.name} (ID: {product.id})")
    except Exception as e:
        print(f"Error fetching product: {e}")
        return

    # 3. Simulate Request Data
    # Payload: {"client": 7, "montant": 10000.0, "date_souhaitee": "2026-01-29T15:22:38.669428", 
    #           "agent": null, "statut": "pending", "delivery_latitude": 6.1256632, 
    #           "delivery_longitude": 1.2101405, "items_data": [{"product": 7, "quantity": 4}]}
    
    data = {
        "items_data": [{"product": product.id, "quantity": 4}],
        "delivery_latitude": 6.1256632,
        "delivery_longitude": 1.2101405,
        "date_souhaitee": timezone.now().isoformat() 
    }
    
    print(f"Testing Serializer with data: {data}")

    # 4. Instantiate and Validate Serializer
    try:
        serializer = CommandeSerializer(data=data)
        if serializer.is_valid():
            print("Serializer is valid.")
            
            # 5. Save
            try:
                print("Attempting to save...")
                commande = serializer.save(client=client)
                print(f"SUCCESS! Commande created: ID {commande.id}")
                print(f"Total Amount: {commande.montant}")
                print(f"Items count: {commande.items.count()}")
            except Exception as e:
                print("BOOTSTRAP ERROR during save():")
                import traceback
                traceback.print_exc()
        else:
            print("Serializer Validation Failed:")
            print(serializer.errors)
    except Exception as e:
        print("General Error during debug:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()
