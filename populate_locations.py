"""
Script standalone pour peupler les localisations d'agents depuis le backend
Ce script se connecte directement à la base de données Django
"""
import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire backend au Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Maintenant importer les modèles Django
from django.core.management import call_command

if __name__ == '__main__':
    print("Génération des données de géolocalisation pour les agents...")
    try:
        call_command('populate_agent_locations', '--agents', '5', '--history', '10')
        print("\n✓ Données générées avec succès!")
        print("\nPour tester l'API, utilisez:")
        print("  GET /api/logistics/agents/test_location/")
        print("  GET /api/logistics/agents/locations/")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        print("\nAssurez-vous que:")
        print("  1. Les dépendances Python sont installées (pip install -r requirements.txt)")
        print("  2. La base de données est accessible")
        print("  3. Les migrations sont à jour (python manage.py migrate)")
