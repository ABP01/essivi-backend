import logging
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from .models import Commande, Livraison, Notification
# We use string references or local imports for User if needed to avoid circular imports, 
# but usually CustomUser is safe if fetched via get_user_model() or imported if no cycle exists.
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger('apps.sales')

def send_push_notification_async(user_id, title, message):
    """
    Background task to send Firebase push notification.
    Fetches user and preferences inside the thread to avoid passing complex objects.
    """
    try:
        from apps.users.models import CustomUser
        try:
            user = CustomUser.objects.get(id=user_id)
            prefs = getattr(user, 'preferences', None)
            token = getattr(prefs, 'fcm_token', None) if prefs else None
            
            if token:
                from apps.users.appwrite_views import initialize_firebase
                from firebase_admin import messaging
                initialize_firebase()
                
                msg = messaging.Message(
                    notification=messaging.Notification(title=title, body=message),
                    token=token,
                )
                messaging.send(msg)
        except CustomUser.DoesNotExist:
            pass
            
    except Exception:
        logger.exception(f"Async push failed for user_id={user_id}")

def trigger_async_push(user, title, message):
    if not user:
        return
    # Launch thread
    t = threading.Thread(target=send_push_notification_async, args=(user.id, title, message))
    t.daemon = True
    t.start()

@receiver(post_save, sender=Commande)
def commande_post_save(sender, instance, created, **kwargs):
    """Handle notifications for Commande."""
    try:
        # 1. Notify Assigned Agent
        if instance.agent:
            msg = f"La commande #{instance.id} vous a été assignée."
            # Check for existing notification to avoid spam
            exists = Notification.objects.filter(
                user=instance.agent, 
                message__icontains=f"commande #{instance.id}"
            ).exists()
            
            if not exists:
                notif = Notification.objects.create(
                    user=instance.agent, 
                    title='Nouvelle commande', 
                    message=msg, 
                    type='info'
                )
                trigger_async_push(instance.agent, notif.title, notif.message)

        # 2. Status 'delivered' -> Notify Client, Admins, Credit Agent
        if instance.statut == 'delivered':
            # Check duplicate for client
            exists_delivered = Notification.objects.filter(
                user=instance.client, 
                message__icontains=f"commande #{instance.id} a été livrée"
            ).exists()
            
            if not exists_delivered:
                # Notify Client
                msg_client = f'Votre commande #{instance.id} a été livrée.'
                notif = Notification.objects.create(
                    user=instance.client, 
                    title='Commande livrée', 
                    message=msg_client, 
                    type='success'
                )
                trigger_async_push(instance.client, notif.title, notif.message)

                # Notify Admins
                try:
                    # Avoid direct import of CustomUser if possible, use User model
                    admins = User.objects.filter(role__in=['admin', 'gestionnaire'])
                    for admin in admins:
                        Notification.objects.create(
                            user=admin, 
                            title='Commande livrée', 
                            message=f'Commande #{instance.id} livrée.', 
                            type='info'
                        )
                except Exception:
                    logger.exception('Failed to notify admins')

                # Credit Agent (500 FCFA)
                if instance.agent and hasattr(instance.agent, 'agent_profile'):
                    try:
                        profile = instance.agent.agent_profile
                        from decimal import Decimal
                        profile.solde += Decimal('500.00')
                        profile.save()
                        logger.info(f"Agent {instance.agent.username} credited 500 FCFA")
                        
                        # Notify Agent about earnings
                        Notification.objects.create(
                            user=instance.agent, 
                            title='Gain reçu', 
                            message=f'Vous avez reçu 500 FCFA pour la livraison #{instance.id}.', 
                            type='success'
                        )
                        # We typically don't push notify for earnings to avoid spam, or we can:
                        # trigger_async_push(instance.agent, 'Gain reçu', ...)
                    except Exception as e:
                        logger.exception(f"Failed to credit agent: {e}")

    except Exception:
        logger.exception('Error in commande_post_save signal')

@receiver(post_save, sender=Livraison)
def livraison_post_save(sender, instance, created, **kwargs):
    """Handle notifications for Livraison."""
    try:
        if instance.statut_livraison == 'en_route':
            exists = Notification.objects.filter(
                user=instance.client, 
                message__icontains="livreur est en route"
            ).exists()
            
            if not exists:
                msg = "Votre livreur est en route !"
                notif = Notification.objects.create(
                    user=instance.client, 
                    title='Livraison en route', 
                    message=msg, 
                    type='info'
                )
                trigger_async_push(instance.client, notif.title, notif.message)
                
    except Exception:
        logger.exception('Error in livraison_post_save signal')
