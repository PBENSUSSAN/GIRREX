# Fichier : activites/models/vol.py

from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

# On importe les modèles de l'application 'core'
from core.models import Agent, Centre, TypeActiviteHorsVol

class Vol(models.Model):
    """
    Représente un bloc de temps sur une timeline : un segment de vol, une relève,
    ou une activité hors-vol (repas, réunion...).
    """
    class TypeFlux(models.TextChoices):
        CAM = 'CAM', 'CAM'
        CAG_ACS = 'CAG_ACS', 'CAG - ACS'
        CAG_APS = 'CAG_APS', 'CAG - APS'
        TOUR = 'TOUR', 'Position TOUR'

    class Statut(models.TextChoices):
        DEMANDE = 'DEMANDE', 'Demandé'
        PLANIFIE = 'PLANIFIE', 'Planifié'
        ASSIGNE = 'ASSIGNE', 'Assigné'
        TERMINE = 'TERMINE', 'Terminé'
        CONSOLIDE = 'CONSOLIDE', 'Consolidé'
        ANNULE = 'ANNULE', 'Annulé'

    # --- Données de Planification ---
    numero_strip = models.CharField(max_length=50, blank=True)
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='vols')
    numero_commande = models.CharField(max_length=100, blank=True)
    date_vol = models.DateField()
    heure_debut_prevue = models.TimeField(verbose_name="Heure de début prévue")
    duree_prevue = models.DurationField(
        verbose_name="Durée prévue",
        help_text="Format: HH:MM:SS",
        default=timedelta(0)
    )
    indicatif = models.CharField(max_length=100, blank=True, verbose_name="Indicatif du vol")
    flux = models.CharField(max_length=10, choices=TypeFlux.choices)

    # --- Données de Réalisation (remplies par le CDQ) ---
    heure_debut_reelle = models.TimeField(
        verbose_name="Heure de début réelle", 
        null=True, blank=True
    )
    heure_fin_reelle = models.TimeField(
        verbose_name="Heure de fin réelle", 
        null=True, blank=True
    )
    
    # --- Champs de Workflow et de Structure ---
    parent_vol = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='releves',
        verbose_name="Vol d'origine (mission)"
    )
    statut = models.CharField(
        max_length=20, 
        choices=Statut.choices, 
        default=Statut.DEMANDE
    )
    nom_cabine = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Nom de la cabine/position assignée par la CCA ou le Planificateur Local."
    )

    # --- Champs pour les Activités Hors-Vol ---
    est_activite_hors_vol = models.BooleanField(default=False)
    type_activite_hors_vol = models.ForeignKey(
        TypeActiviteHorsVol, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    @property
    def duree_reelle(self):
        """ Calcule la durée réelle du vol en heures (float). """
        if not self.heure_debut_reelle or not self.heure_fin_reelle:
            return 0.0
        start = datetime.combine(self.date_vol, self.heure_debut_reelle)
        end = datetime.combine(self.date_vol, self.heure_fin_reelle)
        if end < start:
            end += timedelta(days=1)
        return (end - start).total_seconds() / 3600

    def __str__(self):
        if self.est_activite_hors_vol and self.type_activite_hors_vol:
            return f"{self.type_activite_hors_vol.nom} le {self.date_vol}"
        return f"Vol {self.indicatif or self.numero_strip} du {self.date_vol} à {self.centre.code_centre}"

class SaisieActivite(models.Model):
    class Role(models.TextChoices):
        CONTROLEUR = 'CONTROLEUR', 'Contrôleur en Charge'
        STAGIAIRE = 'STAGIAIRE', 'Contrôleur Stagiaire'
        ISP = 'ISP', 'Instructeur sur Position (ISP)'
        CDQ = 'CDQ', 'Chef de Quart (CDQ)'
        SUPERVISEUR = 'SUPERVISEUR', 'Superviseur'

    vol = models.ForeignKey(Vol, on_delete=models.CASCADE, related_name='activites')
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='activites')
    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta:
        verbose_name = "Saisie d'activité"
        verbose_name_plural = "Saisies d'activité"
        unique_together = ('vol', 'agent')

    def __str__(self):
        return f"{self.agent.trigram} en tant que {self.get_role_display()} sur le vol {self.vol_id}"

    def clean(self):
        """
        La logique de validation complexe est maintenant gérée dans activites/forms.py.
        """
        super().clean()