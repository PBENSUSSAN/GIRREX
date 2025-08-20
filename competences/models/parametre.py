# Fichier : competences/models/parametre.py

from django.db import models
from core.models import Centre

class RegleDeRenouvellement(models.Model):
    """
    Définit un jeu de conditions d'heures requises pour le renouvellement
    des MUA dans un ou plusieurs centres.
    """
    nom = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nom unique de ce jeu de règles (ex: 'Standard National 2025')"
    )
    centres = models.ManyToManyField(
        Centre,
        related_name='regles_renouvellement',
        help_text="Sélectionnez le(s) centre(s) auquel/auxquels cette règle s'applique."
    )
    
    # --- LES SEUILS REQUIS ---
    # Laisser un champ à 0 si non applicable pour ce jeu de règles.
    
    seuil_heures_total = models.PositiveIntegerField(
        default=90,
        verbose_name="Objectif d'heures TOTALES (activité globale)",
    )
    seuil_heures_cam = models.PositiveIntegerField(
        default=40,
        verbose_name="Objectif d'heures spécifiques CAM",
    )
    seuil_heures_cag_acs = models.PositiveIntegerField(
        default=50,
        verbose_name="Objectif d'heures spécifiques CAG ACS",
    )
    seuil_heures_cag_aps = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif d'heures spécifiques CAG APS (si applicable)",
    )
    seuil_heures_tour = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif d'heures spécifiques TOUR (si applicable)",
    )

    class Meta:
        verbose_name = "Jeu de Règles de Renouvellement"
        verbose_name_plural = "Jeux de Règles de Renouvellement"

    def __str__(self):
        return self.nom