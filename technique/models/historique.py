# Fichier : technique/models/historique.py

from django.db import models
from django.conf import settings
from .miso import Miso

class MisoHistorique(models.Model):
    """
    Trace toutes les modifications apportées à un préavis MISO.
    """
    class TypeEvenement(models.TextChoices):
        CREATION = 'CREATION', 'Création du préavis'
        MODIFICATION = 'MODIFICATION', 'Modification des détails'
        ANNULATION = 'ANNULATION', 'Annulation du préavis'

    miso = models.ForeignKey(
        Miso,
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
        help_text="Détails de l'événement au format JSON (ex: motif d'annulation)"
    )

    class Meta:
        verbose_name = "Historique MISO"
        verbose_name_plural = "Historiques MISO"
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d')}] {self.get_type_evenement_display()} sur {self.miso_id}"