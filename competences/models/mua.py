# Fichier : competences/models/mua.py

from django.db import models
from .qualification import Qualification

class MentionUniteAnnuelle(models.Model):
    """
    Le "contrat annuel". Représente le droit d'exercer un flux donné 
    (CAM ou CAG) pour une période d'un an, et centralise le suivi des compétences.
    """
    class TypeFlux(models.TextChoices):
        CAM = 'CAM', 'CAM'
        CAG = 'CAG', 'CAG'

    class Statut(models.TextChoices):
        ACTIF = 'ACTIF', 'Actif'
        SUSPENDU_INACTIVITE = 'SUSPENDU_INACTIVITE', 'Suspendu (inactivité > 90j)'
        SUSPENDU_MANUEL = 'SUSPENDU_MANUEL', 'Suspendu (décision manuelle)'
        EN_ATTENTE_RENOUVELLEMENT = 'EN_ATTENTE_RENOUVELLEMENT', 'En attente de renouvellement'
        ARCHIVE = 'ARCHIVE', 'Archivé (renouvelé ou muté)'

    # La MUA est liée à la qualification active qui lui donne son droit d'exister
    qualification = models.ForeignKey(
        Qualification, 
        on_delete=models.PROTECT, 
        related_name='muas'
    )
    type_flux = models.CharField(
        max_length=3, 
        choices=TypeFlux.choices
    )
    date_debut_cycle = models.DateField()
    date_fin_cycle = models.DateField()
    statut = models.CharField(
        max_length=30, 
        choices=Statut.choices, 
        default=Statut.ACTIF
    )
    annee_cycle = models.PositiveSmallIntegerField(
        default=1, 
        help_text="Numéro de l'année dans le cycle de 3 ans pour le test triennal."
    )
    date_derniere_activite = models.DateField(
        null=True, blank=True,
        help_text="Date du dernier vol enregistré pour cette MUA."
    )

    # --- Compteurs d'heures pour l'année en cours ---
    heures_cam_effectuees = models.FloatField(default=0.0)
    heures_cag_acs_effectuees = models.FloatField(default=0.0)
    heures_cag_aps_effectuees = models.FloatField(default=0.0)
    heures_tour_effectuees = models.FloatField(default=0.0)
    heures_en_cdq = models.FloatField(default=0.0)
    heures_en_supervision = models.FloatField(default=0.0)

    class Meta:
        verbose_name = "Mention d'Unité Annuelle (MUA)"
        verbose_name_plural = "Mentions d'Unité Annuelles (MUA)"
        ordering = ['-date_debut_cycle']

    def __str__(self):
        agent = self.qualification.brevet.agent
        return f"MUA {self.get_type_flux_display()} pour {agent.trigram} ({self.date_debut_cycle.year}-{self.date_fin_cycle.year})"