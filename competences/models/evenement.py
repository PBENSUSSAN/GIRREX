# Fichier : competences/models/evenement.py

from django.db import models
from django.conf import settings
from core.models import Agent

class EvenementCarriere(models.Model):
    """
    Trace un événement notable dans la carrière d'un agent qui peut impacter
    le suivi de ses compétences (ex: arrêt maladie long).
    """
    class TypeEvenement(models.TextChoices):
        SUSPENSION_MANUELLE = 'SUSPENSION_MANUELLE', 'Suspension Manuelle de MUA'
        REPRISE_ACTIVITE = 'REPRISE_ACTIVITE', 'Reprise d\'activité'
        AUTRE = 'AUTRE', 'Autre'

    agent = models.ForeignKey(
        Agent, 
        on_delete=models.PROTECT, 
        related_name='evenements_carriere'
    )
    type_evenement = models.CharField(
        max_length=30, 
        choices=TypeEvenement.choices
    )
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    details = models.TextField(
        verbose_name="Motif / Détails",
        help_text="Raison de l'événement (ex: 'Arrêt médical', 'Détachement', etc.)"
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Événement de carrière"
        verbose_name_plural = "Événements de carrière"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.get_type_evenement_display()} pour {self.agent.trigram} le {self.date_debut}"