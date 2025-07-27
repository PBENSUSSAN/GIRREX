# Fichier : core/models/zone.py

from django.db import models
from django.utils import timezone
from .rh import Agent, Centre
from .service_journalier import ServiceJournalier

class Zone(models.Model):
    """
    Définit une zone géographique ou fonctionnelle spécifique à un centre.
    Ex: 'Piste 2', 'Hangar H5', 'Zone de tir Alpha'.
    """
    nom = models.CharField(
        max_length=100,
        help_text="Nom court et clair de la zone."
    )
    description = models.TextField(
        blank=True,
        help_text="Description plus détaillée de la zone et de ses limites ou fonctions."
    )
    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name='zones',
        help_text="Le centre auquel cette zone est rattachée."
    )
    # Ces champs sont là pour un accès rapide à l'état actuel.
    # Ils seront mis à jour par la logique métier à chaque nouvelle activité.
    est_active = models.BooleanField(
        default=False,
        verbose_name="Actuellement active"
    )
    derniere_activite = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Dernière activité"
    )
    dernier_agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='zones_modifiees',
        verbose_name="Dernier agent intervenu"
    )

    class Meta:
        verbose_name = "Zone"
        verbose_name_plural = "Zones"
        unique_together = ('centre', 'nom') # Assure qu'une zone a un nom unique par centre
        ordering = ['centre', 'nom']
        # On définit les permissions ici pour qu'elles soient créées dans la BDD
        

    def __str__(self):
        return f"{self.nom} ({self.centre.code_centre})"


class ActiviteZone(models.Model):
    """
    Trace un événement d'activation ou de désactivation d'une zone.
    Ceci est l'historique qui sera affiché dans le cahier de marche.
    """
    class TypeAction(models.TextChoices):
        ACTIVATION = 'ACTIVATION', 'Activation'
        DESACTIVATION = 'DESACTIVATION', 'Désactivation'

    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name='historique_activites'
    )
    type_action = models.CharField(
        max_length=20,
        choices=TypeAction.choices,
        verbose_name="Type d'action"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Horodatage de l'action"
    )
    agent_action = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        verbose_name="Agent ayant effectué l'action"
    )
    service_journalier = models.ForeignKey(
        ServiceJournalier,
        on_delete=models.CASCADE,
        related_name='activites_zone_du_jour',
        help_text="Lie l'activité au service journalier qui était ouvert."
    )
    
    class Meta:
        verbose_name = "Activité de Zone"
        verbose_name_plural = "Activités des Zones"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.type_action} de la zone '{self.zone.nom}' par {self.agent_action}"