import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger('apps.sales')


@receiver(post_save)
def sales_post_save(sender, instance, created, **kwargs):
    """Handle notifications for Commande and Livraison.

    - If `Commande.agent` is assigned (and no similar notification exists), notify the agent.
    - If `Commande.statut` == 'delivered', notify client and admins.
    - If `Livraison.statut_livraison` == 'en_route', notify client.
    """
    try:
        from .models import Commande, Livraison, Notification
        from apps.users.models import CustomUser

        # Commande notifications
        if isinstance(instance, Commande):
            # Notify agent when assigned (avoid duplicating)
            if instance.agent is not None:
                msg = f"La commande #{instance.id} vous a été assignée."
                exists = Notification.objects.filter(user=instance.agent, message__icontains=f"commande #{instance.id}").exists()
                if not exists:
                    notif = Notification.objects.create(user=instance.agent, title='Nouvelle commande', message=msg, type='info')
                    try:
                        from apps.users.appwrite_views import initialize_firebase
                        initialize_firebase()
                        prefs = getattr(instance.agent, 'preferences', None)
                        token = getattr(prefs, 'fcm_token', None) if prefs else None
                        if token:
                            from firebase_admin import messaging
                            msg = messaging.Message(
                                notification=messaging.Notification(title=notif.title, body=notif.message),
                                token=token,
                            )
                            messaging.send(msg)
                    except Exception:
                        logger.exception('Failed to send push for commande assigned %s', instance.id)

            # Notify client and admins when Delivered, and Credit Agent
            if instance.statut == 'delivered':
                # Avoid duplicate processing by checking if client notification already exists
                exists_delivered = Notification.objects.filter(user=instance.client, message__icontains=f"commande #{instance.id} a été livrée").exists()
                
                if not exists_delivered:
                    # 1. Notify Client
                    try:
                        notif = Notification.objects.create(user=instance.client, title='Commande livrée', message=f'Votre commande #{instance.id} a été livrée.', type='success')
                        try:
                            from apps.users.appwrite_views import initialize_firebase
                            initialize_firebase()
                            prefs = getattr(instance.client, 'preferences', None)
                            token = getattr(prefs, 'fcm_token', None) if prefs else None
                            if token:
                                from firebase_admin import messaging
                                msg = messaging.Message(
                                    notification=messaging.Notification(title=notif.title, body=notif.message),
                                    token=token,
                                )
                                messaging.send(msg)
                        except Exception:
                            logger.exception('Failed to send push for commande delivered %s', instance.id)
                    except Exception:
                        logger.exception('Failed to notify client for commande %s', instance.id)

                    # 2. Notify Admins
                    try:
                        admins = CustomUser.objects.filter(role__in=['admin', 'gestionnaire'])
                        for admin in admins:
                            Notification.objects.create(user=admin, title='Commande livrée', message=f'Commande #{instance.id} livrée.', type='info')
                    except Exception:
                        logger.exception('Failed to notify admins for commande %s', instance.id)

                    # 3. Credit Agent (500 FCFA)
                    # "à chaque livraison effectué l'agent gagne 500 francs"
                    if instance.agent and hasattr(instance.agent, 'agent_profile'):
                        try:
                            profile = instance.agent.agent_profile
                            # Ensure we are using Decimal or int correctly. solde is Decimal.
                            from decimal import Decimal
                            profile.solde += Decimal('500.00')
                            profile.save()
                            logger.info(f"Agent {instance.agent.username} credited 500 FCFA for order #{instance.id}")
                            
                            # Optional: Notify agent of earnings
                            Notification.objects.create(
                                user=instance.agent, 
                                title='Gain reçu', 
                                message=f'Vous avez reçu 500 FCFA pour la livraison #{instance.id}.', 
                                type='success'
                            )
                        except Exception as e:
                            logger.exception(f"Failed to credit agent {instance.agent.username}: {e}")

        # Livraison notifications
        if isinstance(instance, Livraison):
            if instance.statut_livraison == 'en_route':
                exists = Notification.objects.filter(user=instance.client, message__icontains=f"livreur est en route").exists()
                if not exists:
                    notif = Notification.objects.create(user=instance.client, title='Livraison en route', message="Votre livreur est en route !", type='info')
                    # Try to send push if token available
                    try:
                        from apps.users.appwrite_views import initialize_firebase
                        initialize_firebase()
                        token = getattr(instance.client.preferences, 'fcm_token', None)
                        if token:
                            from firebase_admin import messaging
                            msg = messaging.Message(
                                notification=messaging.Notification(title=notif.title, body=notif.message),
                                token=token,
                            )
                            messaging.send(msg)
                    except Exception:
                        logger.exception('Failed to send push for livraison en_route %s', instance.id)

    except Exception:
        logger.exception('Error in sales_post_save signal')
