from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Agent, Centre
from technique.models.panne import PanneCentre

class PanneCentreModelTests(TestCase):
    """
    Tests for the PanneCentre model.
    """

    def setUp(self):
        """
        Set up the necessary objects for the tests.
        This method is run before each test.
        """
        # 1. Create a User, as Agent has a OneToOneField to it.
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )

        # 2. Create a Centre, as both Agent and PanneCentre need it.
        self.centre = Centre.objects.create(
            nom_centre='Centre de Test',
            code_centre='TEST'
        )

        # 3. Create an Agent.
        self.agent = Agent.objects.create(
            id_agent=1,
            user=self.user,
            centre=self.centre,
            trigram='TST'
        )

    def test_create_panne_centre(self):
        """
        Tests that a PanneCentre instance can be created successfully.
        """
        # Check initial state
        self.assertEqual(PanneCentre.objects.count(), 0)

        # Create the PanneCentre instance
        panne = PanneCentre.objects.create(
            type_equipement=PanneCentre.TypeEquipement.RADAR,
            equipement_details="Radar principal TWR-NORD",
            date_heure_debut=timezone.now(),
            description="L'écran du radar principal est noir.",
            criticite=PanneCentre.Criticite.CRITIQUE,
            centre=self.centre,
            auteur=self.agent
        )

        # Verify the object was created
        self.assertEqual(PanneCentre.objects.count(), 1)

        # Verify some attributes of the created object
        created_panne = PanneCentre.objects.first()
        self.assertEqual(created_panne.pk, panne.pk)
        self.assertEqual(created_panne.auteur, self.agent)
        self.assertEqual(created_panne.centre, self.centre)
        self.assertEqual(created_panne.get_criticite_display(), 'Critique (impact opérationnel direct)')
        self.assertEqual(created_panne.statut, PanneCentre.Statut.EN_COURS)

        # Test the __str__ representation
        expected_str = f"Panne Radar sur TEST le {panne.date_heure_debut.strftime('%d/%m/%Y')}"
        self.assertEqual(str(panne), expected_str)
