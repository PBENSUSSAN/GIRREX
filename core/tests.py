# Fichier : core/tests.py

from django.test import TestCase
from datetime import date, time, timedelta
from types import SimpleNamespace # Un petit outil pratique pour simuler des objets

# On importe la fonction que l'on veut tester
from .services import _calculer_duree_travail

class ServicesCoreTests(TestCase):
    """
    Cette classe va regrouper tous nos tests pour les fonctions
    du fichier services.py de l'application 'core'.
    """

    def test_calcul_duree_journee_simple(self):
        """
        Vérifie que la durée est calculée correctement pour une vacation de jour normale.
        (Exemple : 08:00 -> 16:00 doit donner 8 heures)
        """
        # 1. PRÉPARATION (Arrange)
        faux_pointage = SimpleNamespace(
            date_jour=date(2025, 8, 18),
            heure_arrivee=time(8, 0),
            heure_depart=time(16, 0)
        )

        # 2. ACTION (Act)
        duree_calculee, _, _ = _calculer_duree_travail(faux_pointage)

        # 3. VÉRIFICATION (Assert)
        duree_attendue = timedelta(hours=8)
        self.assertEqual(duree_calculee, duree_attendue)

    def test_calcul_duree_vacation_de_nuit(self):
        """
        Vérifie que la durée est correcte pour une vacation à cheval sur deux jours.
        (Exemple : 22:00 -> 06:00 doit donner 8 heures)
        """
        # 1. PRÉPARATION
        faux_pointage_nuit = SimpleNamespace(
            date_jour=date(2025, 8, 18),
            heure_arrivee=time(22, 0),
            heure_depart=time(6, 0) # L'heure de départ est "avant" l'arrivée
        )

        # 2. ACTION
        duree_calculee, _, _ = _calculer_duree_travail(faux_pointage_nuit)

        # 3. VÉRIFICATION
        duree_attendue = timedelta(hours=8)
        self.assertEqual(duree_calculee, duree_attendue)