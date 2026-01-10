"""
Script pour créer des données de test pour l'application Essivi
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.users.models import CustomUser, UserPreferences
from apps.sales.models import FAQ, Subscription, Notification, BottleReturn
from decimal import Decimal

def create_test_data():
    print("🚀 Création des données de test...")
    
    # 1. Créer des FAQs
    print("\n📚 Création des FAQs...")
    faqs_data = [
        {
            'question': 'Comment passer une commande ?',
            'answer': 'Appuyez sur le bouton "Nouvelle Commande" sur l\'écran d\'accueil, sélectionnez la taille de la bouteille (5L, 10L ou 20L), la quantité, la date et l\'heure de livraison souhaitées, puis confirmez votre commande.',
            'category': 'orders',
            'order': 1
        },
        {
            'question': 'Quels sont les modes de paiement acceptés ?',
            'answer': 'Nous acceptons le paiement en espèces à la livraison, Mobile Money (MTN, Moov, Togocel) et les cartes bancaires.',
            'category': 'payment',
            'order': 2
        },
        {
            'question': 'Comment suivre ma livraison ?',
            'answer': 'Vous pouvez suivre votre livraison en temps réel depuis l\'écran "Suivi" de l\'application. Vous verrez la position du livreur et le temps estimé d\'arrivée.',
            'category': 'delivery',
            'order': 3
        },
        {
            'question': 'Comment créer un abonnement ?',
            'answer': 'Allez dans l\'onglet "Abonnement", choisissez votre plan (hebdomadaire, bi-mensuel ou mensuel), sélectionnez la taille et la quantité de bouteilles, puis confirmez.',
            'category': 'subscription',
            'order': 4
        },
        {
            'question': 'Comment retourner des bouteilles vides ?',
            'answer': 'Allez dans "Retour de bouteilles", indiquez le nombre de bouteilles à retourner. Un crédit sera ajouté à votre compte après validation.',
            'category': 'returns',
            'order': 5
        },
        {
            'question': 'Quelle est la qualité de l\'eau ?',
            'answer': 'Notre eau provient de sources naturelles protégées et est certifiée ISO 9001:2015, HACCP et Bio. Consultez l\'écran "Qualité de l\'eau" pour plus de détails.',
            'category': 'quality',
            'order': 6
        },
    ]
    
    for faq_data in faqs_data:
        faq, created = FAQ.objects.get_or_create(
            question=faq_data['question'],
            defaults=faq_data
        )
        if created:
            print(f"  ✅ FAQ créée : {faq.question[:50]}...")
        else:
            print(f"  ⏭️  FAQ existe déjà : {faq.question[:50]}...")
    
    # 2. Créer des préférences pour les utilisateurs existants
    print("\n⚙️  Création des préférences utilisateur...")
    clients = CustomUser.objects.filter(role='client')
    for client in clients[:5]:  # Limiter aux 5 premiers clients
        prefs, created = UserPreferences.objects.get_or_create(
            user=client,
            defaults={
                'notifications_enabled': True,
                'email_notifications': True,
                'sms_notifications': False,
                'language': 'fr'
            }
        )
        if created:
            print(f"  ✅ Préférences créées pour : {client.email}")
        else:
            print(f"  ⏭️  Préférences existent pour : {client.email}")
    
    # 3. Créer des notifications de test
    print("\n🔔 Création des notifications...")
    if clients.exists():
        client = clients.first()
        notifications_data = [
            {
                'user': client,
                'title': 'Bienvenue sur Essivi !',
                'message': 'Merci de nous faire confiance pour votre livraison d\'eau. Passez votre première commande dès maintenant !',
                'type': 'info'
            },
            {
                'user': client,
                'title': 'Promotion spéciale',
                'message': 'Profitez de 10% de réduction sur votre prochain abonnement mensuel !',
                'type': 'success'
            },
        ]
        
        for notif_data in notifications_data:
            notif, created = Notification.objects.get_or_create(
                user=notif_data['user'],
                title=notif_data['title'],
                defaults=notif_data
            )
            if created:
                print(f"  ✅ Notification créée : {notif.title}")
            else:
                print(f"  ⏭️  Notification existe : {notif.title}")
    
    # 4. Créer un abonnement de test
    print("\n📅 Création d\'abonnements de test...")
    if clients.exists():
        client = clients.first()
        subscription, created = Subscription.objects.get_or_create(
            client=client,
            defaults={
                'plan': 'mensuel',
                'bottle_size': '20L',
                'quantity': 4,
                'preferred_day': 'Lundi',
                'time_slot': '09:00 - 12:00',
                'status': 'active'
            }
        )
        if created:
            print(f"  ✅ Abonnement créé pour : {client.email}")
        else:
            print(f"  ⏭️  Abonnement existe pour : {client.email}")
    
    print("\n✅ Données de test créées avec succès !")
    print("\n📊 Résumé :")
    print(f"  - FAQs : {FAQ.objects.count()}")
    print(f"  - Préférences : {UserPreferences.objects.count()}")
    print(f"  - Notifications : {Notification.objects.count()}")
    print(f"  - Abonnements : {Subscription.objects.count()}")
    print(f"  - Retours de bouteilles : {BottleReturn.objects.count()}")

if __name__ == '__main__':
    create_test_data()
