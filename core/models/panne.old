# Fichier : core/models/panne.py

from django.db import models
from .rh import Agent, Centre

class PanneCentre(models.Model):
    """
    Consigne une panne sur un équipement ou un système du centre.
    """
    class Criticite(models.TextChoices):
        CRITIQUE = 'CRITIQUE', 'Critique (impact opérationnel direct)'
        MAJEURE = 'MAJEURE', 'Majeure (dégradation notable)'
        MINEURE = 'MINEURE', 'Mineure (gêne ou problème de confort)'

    class Statut(models.TextChoices):
        EN_COURS = 'EN_COURS', 'En cours'
        RESOLUE = 'RESOLUE', 'Résolue'

    equipement_concerne = models.CharField(
        max_length=255,
        help_text="Nom du système ou de l'équipement en panne."
    )
    date_heure_debut = models.DateTimeField(
        db_index=True,
        help_text="Date et heure du début de la panne."
    )
    date_heure_fin = models.DateTimeField(
        null=True, blank=True,
        help_text="Date et heure de la résolution de la panne (laisser vide si en cours)."
    )
    criticite = models.CharField(
        max_length=20,
        choices=Criticite.choices,
        default=Criticite.MINEURE
    )
    description = models.TextField(
        help_text="Description de la panne et de son impact."
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_COURS
    )
    centre = models.ForeignKey(
        Centre,
        on_delete=models.PROTECT,
        related_name='pannes'
    )
    auteur = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        related_name='pannes_consignees'
    )
    notification_generale = models.BooleanField(
        default=False,
        verbose_name="Signaler pour notification générale",
        help_text="Cochez cette case si cette panne doit faire l'objet d'une notification."
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Panne Centre"
        verbose_name_plural = "Pannes Centre"
        ordering = ['-date_heure_debut']
        permissions = [
            ("resolve_pannecentre", "Peut marquer une panne comme résolue"),
        ]

    def __str__(self):
        return f"Panne de {self.equipement_concerne} sur {self.centre.code_centre} le {self.date_heure_debut.strftime('%d/%m/%Y')}"