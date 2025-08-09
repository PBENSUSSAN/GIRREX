# Fichier : technique/models/panne.py

from django.db import models
from core.models import Agent, Centre

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
        
    # --- NOUVELLE ÉNUMÉRATION POUR LE TYPE D'ÉQUIPEMENT ---
    class TypeEquipement(models.TextChoices):
        RADIO = 'RADIO', 'Radio'
        RADAR = 'RADAR', 'Radar'
        VISU = 'VISU', 'Visualisation'
        TELEPHONE= 'TELEPHONIE', 'Telephone'
        INTERPHONE= 'INTERPHONIE', 'Interphone'
        INFRA = 'INFRA', 'Infrastructure'
        AUTRE = 'AUTRE', 'Autre'

    # --- CHAMPS MODIFIÉS ---
    type_equipement = models.CharField(
        max_length=30,
        choices=TypeEquipement.choices,
        verbose_name="Système concerné",
        default=TypeEquipement.AUTRE
    )
    
    equipement_details = models.CharField(
        max_length=255,
        verbose_name="Précisions sur l'équipement",
        help_text="Nom ou référence exacte de l'équipement en panne.",
        blank=True
    )

    # --- CHAMPS INCHANGÉS ---
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
        # On met à jour la représentation textuelle pour qu'elle soit plus claire
        return f"Panne {self.get_type_equipement_display()} sur {self.centre.code_centre} le {self.date_heure_debut.strftime('%d/%m/%Y')}"