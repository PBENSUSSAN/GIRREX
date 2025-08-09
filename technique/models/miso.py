# Fichier : technique/models/miso.py

from django.db import models
from django.utils import timezone
from core.models import Agent, Centre

class Miso(models.Model):
    """
    Représente un préavis de Maintenance d'Installation et de Service Opérationnel (MISO).
    """

    # --- Énumérations (Choices) pour les champs contrôlés ---
    
    class TypeMaintenance(models.TextChoices):
        RADIO = 'RADIO', 'Radio'
        RADAR = 'RADAR', 'Radar'
        VISU = 'VISU', 'Visualisation'
        INFRA = 'INFRA', 'Infrastructure'
        AUTRE = 'AUTRE', 'Autre'

    class Statut(models.TextChoices):
        # Statut manuel, prioritaire sur les statuts calculés
        ANNULE = 'ANNULE', 'Annulé'
        # Les statuts ci-dessous ne sont pas stockés en base, mais calculés dynamiquement.
        # Ils sont définis ici pour être réutilisés dans la logique.
        PLANIFIE = 'PLANIFIE', 'Planifié'
        EN_COURS = 'EN_COURS', 'En cours'
        TERMINE = 'TERMINE', 'Terminé'

    # --- Champs de la base de données ---

    responsable = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        verbose_name="Responsable ES",
        related_name="misos_crees"
    )
    centre = models.ForeignKey(
        Centre,
        on_delete=models.PROTECT,
        verbose_name="Centre concerné",
        related_name="misos"
    )
    date_debut = models.DateTimeField(
        verbose_name="Date et heure de début"
    )
    date_fin = models.DateTimeField(
        verbose_name="Date et heure de fin"
    )
    type_maintenance = models.CharField(
        max_length=20,
        choices=TypeMaintenance.choices,
        verbose_name="Type de maintenance"
    )
    description = models.TextField(
        verbose_name="Description de l'intervention"
    )
    piece_jointe = models.FileField(
        upload_to='miso_attachments/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Pièce jointe"
    )
    # Le seul statut que nous stockons est 'ANNULE'. Les autres sont calculés.
    statut_override = models.CharField(
        max_length=20,
        choices=Statut.choices,
        blank=True, # Peut être vide si le statut est calculé
        null=True,
        verbose_name="Statut manuel (Annulé)"
    )
    
    # Timestamps automatiques
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Propriété dynamique pour le statut ---
    
    @property
    def statut(self):
        """
        Calcule le statut de la MISO de manière dynamique.
        Le statut 'ANNULE' est prioritaire s'il est défini.
        """
        # Si un statut manuel (Annulé) est forcé, il est prioritaire
        if self.statut_override == self.Statut.ANNULE:
            return self.Statut.ANNULE
        
        now = timezone.now()
        if now < self.date_debut:
            return self.Statut.PLANIFIE
        elif self.date_debut <= now < self.date_fin:
            return self.Statut.EN_COURS
        else: # now >= self.date_fin
            return self.Statut.TERMINE

    # --- Configuration du modèle ---

    class Meta:
        verbose_name = "Préavis de Maintenance (MISO)"
        verbose_name_plural = "Préavis de Maintenance (MISO)"
        ordering = ['-date_debut'] # On trie par défaut par date de début la plus récente

    def __str__(self):
        return f"MISO du {self.date_debut.strftime('%d/%m/%Y')} sur {self.centre.code_centre} ({self.get_type_maintenance_display()})"