#!/usr/bin/env python
"""
Script pour supprimer les utilisateurs client et agent
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Supprimer client1
if User.objects.filter(username='client1').exists():
    User.objects.get(username='client1').delete()
    print("✅ client1 supprimé")
else:
    print("⚠️  client1 n'existe pas")

# Supprimer agent1
if User.objects.filter(username='agent1').exists():
    User.objects.get(username='agent1').delete()
    print("✅ agent1 supprimé")
else:
    print("⚠️  agent1 n'existe pas")

print("\n✅ Utilisateurs restants: admin et gestionnaire1 uniquement")
