#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.sales.models import Product

# Create initial products
products = [
    {
        'name': 'Pack Eau 12 sachets',
        'category': 'water',
        'unit': 'pack',
        'quantity_per_unit': 12,
        'price': 6000,
        'description': 'Pack de 12 sachets d\'eau Essivi'
    },
    {
        'name': 'Pack Eau 24 sachets',
        'category': 'water',
        'unit': 'pack',
        'quantity_per_unit': 24,
        'price': 12000,
        'description': 'Pack de 24 sachets d\'eau Essivi'
    },
    {
        'name': 'Pack Boissons 12 canettes',
        'category': 'drink',
        'unit': 'pack',
        'quantity_per_unit': 12,
        'price': 7200,
        'description': 'Pack de 12 canettes de boissons'
    },
    {
        'name': 'Pack Boissons 24 canettes',
        'category': 'drink',
        'unit': 'pack',
        'quantity_per_unit': 24,
        'price': 14400,
        'description': 'Pack de 24 canettes de boissons'
    },
    {
        'name': 'Caisse Eau 5L x 4',
        'category': 'water',
        'unit': 'case',
        'quantity_per_unit': 4,
        'price': 8000,
        'description': 'Caisse de 4 bouteilles d\'eau de 5L'
    },
    {
        'name': 'Caisse Boissons 1.5L x 12',
        'category': 'drink',
        'unit': 'case',
        'quantity_per_unit': 12,
        'price': 18000,
        'description': 'Caisse de 12 bouteilles de boissons de 1.5L'
    },
]

for product_data in products:
    product, created = Product.objects.get_or_create(
        name=product_data['name'],
        defaults=product_data
    )
    if created:
        print(f"Created product: {product.name}")
    else:
        print(f"Product already exists: {product.name}")

print("Product creation completed!")