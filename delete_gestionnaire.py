#!/usr/bin/env python
"""
Script pour supprimer le gestionnaire (garder seulement admin)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Supprimer gestionnaire1
if User.objects.filter(username='gestionnaire1').exists():
    User.objects.get(username='gestionnaire1').delete()
    print("✅ gestionnaire1 supprimé")
else:
    print("⚠️  gestionnaire1 n'existe pas")

print("\n✅ SEUL UTILISATEUR RESTANT:")
print("   Username: admin")
print("   Password: admin123")
