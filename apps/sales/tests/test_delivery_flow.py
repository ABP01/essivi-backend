from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import CustomUser, AgentProfile, ClientProfile
from apps.sales.models import Commande, Livraison
from apps.sales.services import SalesService

class DeliveryFlowTest(TestCase):
    def setUp(self):
        # Users
        self.client_user = CustomUser.objects.create_user(username='client1', password='pass', role='client')
        ClientProfile.objects.create(user=self.client_user, gps_lat=6.1300, gps_lng=1.2200)

        self.agent = CustomUser.objects.create_user(username='agent1', password='pass', role='agent')
        AgentProfile.objects.create(user=self.agent, latitude=6.1305, longitude=1.2205, solde=Decimal('0.00'))

        self.far_agent = CustomUser.objects.create_user(username='agent_far', password='pass', role='agent')
        AgentProfile.objects.create(user=self.far_agent, latitude=10.0, longitude=10.0, solde=Decimal('0.00'))

        self.commande = Commande.objects.create(
            client=self.client_user,
            montant=Decimal('1500.00'),
            date_souhaitee=timezone.now()
        )

    def test_assign_nearest_agent_when_none_provided(self):
        # Assign automatically (no agent_id provided)
        result = SalesService.assign_agent_to_command(self.commande.id, agent_id=None)
        self.commande.refresh_from_db()
        self.assertIsNotNone(self.commande.agent)
        self.assertEqual(self.commande.agent.username, 'agent1')

    def test_client_validation_credits_agent(self):
        # Assign agent explicitly
        SalesService.assign_agent_to_command(self.commande.id, agent_id=self.agent.id)
        livraison = Livraison.objects.get(commande=self.commande)

        # Agent marks delivered via API
        agent_client = APIClient()
        agent_client.force_authenticate(user=self.agent)
        resp = agent_client.post(f'/api/sales/livraisons/{livraison.id}/update_status/', {'statut_livraison': 'delivered', 'gps_lat': 6.1305, 'gps_lng': 1.2205}, format='json')
        self.assertEqual(resp.status_code, 200)

        livraison.refresh_from_db()
        self.assertEqual(livraison.statut_livraison, 'delivered')
        self.assertFalse(livraison.preuve_validee)

        # Capture agent solde before client validation
        agent_profile = self.agent.agent_profile
        initial_solde = agent_profile.solde

        # Client validates
        client_api = APIClient()
        client_api.force_authenticate(user=self.client_user)
        resp2 = client_api.post(f'/api/sales/livraisons/{livraison.id}/client_validate/')
        self.assertEqual(resp2.status_code, 200)

        agent_profile.refresh_from_db()
        self.assertEqual(agent_profile.solde, initial_solde + Decimal('500.00'))

    def test_push_sent_when_notification_created(self):
        # Ensure user has fcm token saved
        prefs = getattr(self.client_user, 'preferences', None)
        if prefs is None:
            from apps.users.models import UserPreferences
            prefs = UserPreferences.objects.create(user=self.client_user, fcm_token='device-token')
        else:
            prefs.fcm_token = 'device-token'
            prefs.save()

        livraison = Livraison.objects.create(tournee_id=1, commande=self.commande, client=self.client_user)

        # Patch firebase messaging.send to assert it's called
        from unittest.mock import patch
        with patch('firebase_admin.messaging.send') as mock_send:
            # Trigger en_route notification
            agent_client = APIClient()
            agent_client.force_authenticate(user=self.agent)
            resp = agent_client.post(f'/api/sales/livraisons/{livraison.id}/update_status/', {'statut_livraison': 'en_route'}, format='json')
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(mock_send.called)
