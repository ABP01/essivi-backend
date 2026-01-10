#!/usr/bin/env python
"""
Script pour créer des utilisateurs de test pour le projet ESSIVI
Usage: python manage.py shell < create_test_users.py
ou: docker compose exec backend python manage.py shell < backend/create_test_users.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import AgentProfile, ClientProfile

User = get_user_model()

def create_test_users():
    """Crée les utilisateurs de test s'ils n'existent pas déjà"""
    
    # 1. ADMIN
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@essivi.com',
            password='admin123',
            role='admin',
            phone_number='+228 90 00 00 01'
        )
        print(f"✅ Admin créé: {admin.username}")
    else:
        print(f"⚠️  Admin existe déjà")
    
    # 2. AGENT
    if not User.objects.filter(username='agent1').exists():
        agent = User.objects.create_user(
            username='agent1',
            email='agent@essivi.com',
            password='agent123',
            first_name='Jean',
            last_name='Dupont',
            role='agent',
            phone_number='+228 90 11 11 11'
        )
        # Créer le profil agent
        AgentProfile.objects.create(
            user=agent,
            zone_assignee='Lomé Centre',
            identification_number='AG001',
            tricycle_plate='TG-123-AB'
        )
        print(f"✅ Agent créé: {agent.username}")
    else:
        print(f"⚠️  Agent existe déjà")
    
    # 3. CLIENT
    if not User.objects.filter(username='client1').exists():
        client = User.objects.create_user(
            username='client1',
            email='client@essivi.com',
            password='client123',
            first_name='Marie',
            last_name='Kouassi',
            role='client',
            phone_number='+228 90 22 22 22'
        )
        # Créer le profil client
        ClientProfile.objects.create(
            user=client,
            nom_point_vente='Boutique Marie',
            nom_proprietaire='Marie Kouassi',
            adresse='Quartier Adidogomé, Lomé',
            gps_lat=6.1256,
            gps_lng=1.2225,
            solde=0
        )
        print(f"✅ Client créé: {client.username}")
    else:
        print(f"⚠️  Client existe déjà")
    
    # 4. GESTIONNAIRE
    if not User.objects.filter(username='gestionnaire1').exists():
        gestionnaire = User.objects.create_user(
            username='gestionnaire1',
            email='gestionnaire@essivi.com',
            password='gestion123',
            first_name='Paul',
            last_name='Mensah',
            role='gestionnaire',
            phone_number='+228 90 33 33 33'
        )
        print(f"✅ Gestionnaire créé: {gestionnaire.username}")
    else:
        print(f"⚠️  Gestionnaire existe déjà")
    
    print("\n" + "="*50)
    print("🎉 INITIALISATION TERMINÉE")
    print("="*50)
    print("\n📋 IDENTIFIANTS DE TEST:\n")
    print("🔐 ADMIN:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("👷 AGENT:")
    print("   Username: agent1")
    print("   Password: agent123")
    print()
    print("🛒 CLIENT:")
    print("   Username: client1")
    print("   Password: client123")
    print()
    print("📊 GESTIONNAIRE:")
    print("   Username: gestionnaire1")
    print("   Password: gestion123")
    print()

if __name__ == '__main__':
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
