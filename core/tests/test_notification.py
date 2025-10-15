# Fichier : core/tests/test_notification.py
"""
Tests pour le système de notifications.
À lancer après avoir ajouté le système de notifications pour vérifier que tout marche.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date

from core.models import Agent, Centre, Notification

class NotificationModelTest(TestCase):
    """Tests du modèle Notification."""
    
    def setUp(self):
        """Configuration initiale pour chaque test."""
        # Créer un centre
        self.centre = Centre.objects.create(
            nom_centre="Centre Test",
            code_centre="CT"
        )
        
        # Créer un utilisateur et son agent
        self.user = User.objects.create_user(
            username='testagent',
            password='testpass123'
        )
        
        self.agent = Agent.objects.create(
            id_agent=1,
            trigram="TST",
            centre=self.centre,
            user=self.user
        )
    
    def test_notification_creation(self):
        """Test de création d'une notification."""
        notif = Notification.objects.create(
            destinataire=self.agent,
            type_notification=Notification.TypeNotification.INFO,
            titre="Test Notification",
            message="Ceci est un test"
        )
        
        self.assertEqual(notif.destinataire, self.agent)
        self.assertEqual(notif.titre, "Test Notification")
        self.assertFalse(notif.lue)
        self.assertIsNone(notif.date_lecture)
    
    def test_marquer_comme_lue(self):
        """Test de la méthode marquer_comme_lue."""
        notif = Notification.objects.create(
            destinataire=self.agent,
            titre="Test",
            message="Test"
        )
        
        # Vérifier qu'elle n'est pas lue au départ
        self.assertFalse(notif.lue)
        self.assertIsNone(notif.date_lecture)
        
        # Marquer comme lue
        notif.marquer_comme_lue()
        
        # Vérifier qu'elle est maintenant lue
        self.assertTrue(notif.lue)
        self.assertIsNotNone(notif.date_lecture)
    
    def test_notification_str(self):
        """Test de la représentation string."""
        notif = Notification.objects.create(
            destinataire=self.agent,
            titre="Ma Notification",
            message="Test"
        )
        
        expected = f"Ma Notification pour {self.agent}"
        self.assertEqual(str(notif), expected)
