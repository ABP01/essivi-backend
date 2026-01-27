import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger('apps.logistics')

@receiver(post_save)
def credit_agent_on_delivery(sender, instance, created, **kwargs):
    """Credit agent when a Livraison is validated and delivered.

    This signal listens broadly and only acts for Livraison instances to avoid
    tight coupling. It credits 500 FCFA to the agent's `AgentProfile.solde`
    when `preuve_validee` is True and `statut_livraison` == 'delivered'.
    """
    try:
        # Import lazily to avoid app registry issues
        from apps.sales.models import Livraison
        if not isinstance(instance, Livraison):
            return

        # Only react when proof validated and marked delivered
        if not (instance.preuve_validee and instance.statut_livraison == 'delivered'):
            return

        # Get associated commande and agent
        commande = getattr(instance, 'commande', None)
        if not commande or not getattr(commande, 'agent', None):
            return

        agent_user = commande.agent

        # Update or create AgentProfile solde safely using F expression
        from django.db.models import F
        from apps.users.models import AgentProfile, CustomUser

        agent_profile = getattr(agent_user, 'agent_profile', None)
        if agent_profile is None:
            # Create profile if missing
            agent_profile = AgentProfile.objects.create(user=agent_user)

        AgentProfile.objects.filter(pk=agent_profile.pk).update(solde=F('solde') + 500)

        # Create notification for client
        from apps.sales.models import Notification
        try:
            Notification.objects.create(
                user=instance.client,
                title='Livraison confirmée',
                message=f'La livraison #{instance.id} a été validée. Le livreur a été crédité de 500 FCFA.',
                type='success'
            )
        except Exception:
            logger.exception('Failed to create client notification for delivery %s', instance.id)

        # Notify admins (database notification entries)
        try:
            from apps.users.models import CustomUser
            admins = CustomUser.objects.filter(role__in=['admin', 'gestionnaire'])
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title='Livraison terminée',
                    message=f'Livraison #{instance.id} marquée livrée par {agent_user.username}.',
                    type='info'
                )
        except Exception:
            logger.exception('Failed to notify admins for delivery %s', instance.id)

    except Exception:
        logger.exception('Error in credit_agent_on_delivery signal')
