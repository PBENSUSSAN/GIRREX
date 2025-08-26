from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Agent, Centre
from .models.brevet import Brevet
from .models.qualification import Qualification

class QualificationModelTests(TestCase):
    """
    Tests for the Qualification model.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up non-modified objects used by all test methods.
        Using setUpTestData is more efficient than setUp for objects
        that don't change during tests.
        """
        # 1. Create Centre
        cls.centre = Centre.objects.create(
            nom_centre='Centre Principal',
            code_centre='MAIN'
        )

        # 2. Create User
        cls.user = User.objects.create_user(
            username='c_test',
            password='password'
        )

        # 3. Create Agent
        cls.agent = Agent.objects.create(
            id_agent=99,
            user=cls.user,
            centre=cls.centre,
            trigram='CTT'
        )

        # 4. Create Brevet for the Agent
        cls.brevet = Brevet.objects.create(
            agent=cls.agent,
            numero_brevet='BVT-99-TEST',
            date_delivrance=timezone.now().date()
        )

    def test_create_qualification(self):
        """
        Tests that a Qualification instance can be created successfully.
        """
        self.assertEqual(Qualification.objects.count(), 0)

        # Create the Qualification instance
        qualification = Qualification.objects.create(
            brevet=self.brevet,
            centre=self.centre,
            type_flux=Qualification.TypeFlux.CAM,
            type_qualification=Qualification.TypeQualification.PC,
            date_obtention=timezone.now().date()
        )

        # Assertions
        self.assertEqual(Qualification.objects.count(), 1)

        created_qual = Qualification.objects.first()
        self.assertEqual(created_qual.brevet, self.brevet)
        self.assertEqual(created_qual.centre, self.centre)
        self.assertEqual(created_qual.get_type_qualification_display(), 'PC')
        self.assertEqual(created_qual.statut, Qualification.Statut.ACTIF)

        # Test the __str__ representation
        expected_str = f"PC pour CTT à MAIN"
        self.assertEqual(str(qualification), expected_str)
