# Fichier : competences/models/parametre.py

from django.db import models
from core.models import Centre

class RegleDeRenouvellement(models.Model):
    """
    Définit une condition à vérifier pour le renouvellement d'une MUA.
    Permet une grande flexibilité dans la configuration des exigences.
    """
    class SourceHeures(models.TextChoices):
        HEURES_CAM = 'heures_cam_effectuees', 'Heures CAM'
        HEURES_CAG_ACS = 'heures_cag_acs_effectuees', 'Heures CAG ACS'
        HEURES_CAG_APS = 'heures_cag_aps_effectuees', 'Heures CAG APS'
        HEURES_TOUR = 'heures_tour_effectuees', 'Heures TOUR'

    nom_regle = models.CharField(
        max_length=255, 
        help_text="Description claire de la règle (ex: 'Quota annuel CAM pour Istres')"
    )
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE,
        help_text="Centre auquel cette règle s'applique."
    )
    type_flux_mua = models.CharField(
        max_length=3,
        choices=[('CAM', 'CAM'), ('CAG', 'CAG')],
        help_text="Type de MUA concernée par cette règle."
    )
    source_heures_1 = models.CharField(
        max_length=30, 
        choices=SourceHeures.choices,
        verbose_name="Source principale d'heures"
    )
    seuil_heures_1 = models.PositiveIntegerField(
        verbose_name="Seuil requis pour la source principale"
    )
    source_heures_2 = models.CharField(
        max_length=30, 
        choices=SourceHeures.choices,
        verbose_name="Source secondaire d'heures (optionnel)",
        blank=True, null=True
    )
    seuil_heures_2 = models.PositiveIntegerField(
        verbose_name="Seuil requis pour la source secondaire",
        blank=True, null=True
    )

    class Meta:
        verbose_name = "Règle de renouvellement"
        verbose_name_plural = "Règles de renouvellement"
        unique_together = ('centre', 'type_flux_mua', 'nom_regle')

    def __str__(self):
        return self.nom_regle