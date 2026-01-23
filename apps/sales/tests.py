"""
Unit tests for Sales Service layer.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.sales.services import SalesService
from apps.sales.models import Commande, Livraison
from apps.logistics.models import Tournee

User = get_user_model()


class SalesServiceTestCase(TestCase):
    """Test cases for SalesService."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.agent = User.objects.create_user(
            username='agent_test',
            email='agent@test.com',
            password='testpass123',
            role='agent'
        )
        
        self.client_user = User.objects.create_user(
            username='client_test',
            email='client@test.com',
            password='testpass123',
            role='client'
        )
        
        # Create test command
        self.commande = Commande.objects.create(
            client=self.client_user,
            statut='pending',
            details='Test order'
        )
    
    def test_assign_agent_to_command_success(self):
        """Test successful agent assignment to command."""
        result = SalesService.assign_agent_to_command(
            commande_id=self.commande.id,
            agent_id=self.agent.id
        )
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['commande_id'], self.commande.id)
        self.assertEqual(result['agent_id'], self.agent.id)
        
        # Verify command was updated
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.agent, self.agent)
        self.assertEqual(self.commande.statut, 'validated')
        
        # Verify Tournee was created
        tournee = Tournee.objects.filter(agent=self.agent).first()
        self.assertIsNotNone(tournee)
        
        # Verify Livraison was created
        livraison = Livraison.objects.filter(commande=self.commande).first()
        self.assertIsNotNone(livraison)
        self.assertEqual(livraison.tournee, tournee)
    
    def test_assign_agent_invalid_agent(self):
        """Test assignment with invalid agent ID."""
        with self.assertRaises(ValueError) as context:
            SalesService.assign_agent_to_command(
                commande_id=self.commande.id,
                agent_id=99999  # Non-existent agent
            )
        
        self.assertIn('Agent', str(context.exception))
    
    def test_assign_agent_invalid_command(self):
        """Test assignment with invalid command ID."""
        with self.assertRaises(ValueError) as context:
            SalesService.assign_agent_to_command(
                commande_id=99999,  # Non-existent command
                agent_id=self.agent.id
            )
        
        self.assertIn('Command', str(context.exception))
    
    def test_assign_non_agent_user(self):
        """Test assignment with non-agent user."""
        with self.assertRaises(ValueError) as context:
            SalesService.assign_agent_to_command(
                commande_id=self.commande.id,
                agent_id=self.client_user.id  # Client, not agent
            )
        
        self.assertIn('not an agent', str(context.exception))


# To run these tests:
# python manage.py test apps.sales.tests.test_services
