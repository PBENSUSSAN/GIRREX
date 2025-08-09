# Fichier : technique/models/historique_panne.py

from django.db import models
from django.conf import settings
from .panne import PanneCentre

class PanneHistorique(models.Model):
    """
    Trace toutes les modifications apportées à une panne.
    """
    class TypeEvenement(models.TextChoices):
        CREATION = 'CREATION', 'Création de la panne'
        MODIFICATION = 'MODIFICATION', 'Modification des détails'
        RESOLUTION = 'RESOLUTION', 'Résolution de la panne'

    panne = models.ForeignKey(
        PanneCentre,
        on_delete=models.CASCADE,
        related_name='historique'
    )
    type_evenement = models.CharField(
        max_length=20,
        choices=TypeEvenement.choices
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Auteur de l'événement"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(
        default=dict,
        help_text="Détails de l'événement (ex: commentaire, changements)"
    )

    class Meta:
        verbose_name = "Historique de Panne"
        verbose_name_plural = "Historiques des Pannes"
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d')}] {self.get_type_evenement_display()} sur Panne #{self.panne_id}"