# Fichier : competences/models/qualification.py

from django.db import models
from django.utils import timezone
from core.models import Centre
from .licence import Licence

class Qualification(models.Model):
    """
    Représente un acquis de carrière, un "diplôme" obtenu par l'agent.
    """
    class TypeQualification(models.TextChoices):
        ACS = 'ACS', 'Contrôle d\'Approche de Surveillance (ACS)'
        ADI = 'ADI', 'Contrôle d\'Aérodrome aux Instruments (ADI)'
        ADV = 'ADV', 'Contrôle d\'Aérodrome à Vue (ADV)'
        CAER = 'CAER', 'CAER'
        PC = 'PC', 'PC'
        CDQ = 'CDQ', 'Chef de Quart'
        ISP = 'ISP', 'Instructeur sur Position'
        EXA = 'EXA', 'Examinateur'

    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name='qualifications')
    type_qualification = models.CharField(max_length=10, choices=TypeQualification.choices)
    date_obtention = models.DateField()
    privileges_actifs = models.BooleanField(default=True, help_text="Décocher si l'agent ne souhaite plus exercer les privilèges optionnels (ISP/EXA).")

    class Meta:
        unique_together = ('licence', 'type_qualification')
        verbose_name = "Qualification"
        verbose_name_plural = "Qualifications"

    def __str__(self):
        return f"{self.licence.agent.trigram} - {self.get_type_qualification_display()}"

class MentionUnite(models.Model):
    """
    Représente le privilège d'exercer dans un centre donné pour un type de trafic (CAM/CAG).
    C'est le contrat d'objectifs pour le maintien de compétences.
    """
    class TypeFlux(models.TextChoices):
        CAM = 'CAM', 'Circulation Aérienne Militaire'
        CAG = 'CAG', 'Circulation Aérienne Générale'
    
    class StatutMention(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE_MUTATION = 'INACTIVE_MUTATION', 'Inactive (suite à mutation)'
        EXPIREE = 'EXPIREE', 'Expirée'

    # ### CORRECTION MAJEURE : La mention est maintenant liée à la Licence directement.
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name='mentions_unite')
    
    # La qualification devient une information contextuelle (Quel diplôme est utilisé pour cette mention ?)
    qualification_source = models.ForeignKey(Qualification, on_delete=models.PROTECT, related_name='mentions_associees')

    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name='mentions_delivrees')
    type_flux = models.CharField(max_length=3, choices=TypeFlux.choices, verbose_name="Type de Mention")
    mention_particuliere = models.CharField(max_length=100, blank=True, verbose_name="Position/Secteur (ex: TOUR)")
    
    date_delivrance = models.DateField()
    date_echeance = models.DateField(verbose_name="Échéance de la mention")
    statut = models.CharField(max_length=20, choices=StatutMention.choices, default=StatutMention.ACTIVE)
    
    heures_requises_annuelles = models.PositiveIntegerField(default=0, verbose_name="Heures requises/an")
    heures_effectuees_cycle = models.FloatField(default=0.0, verbose_name="Heures effectuées (cycle)")
    date_debut_cycle = models.DateField()

    class Meta:
        unique_together = ('licence', 'centre', 'type_flux', 'mention_particuliere')
        verbose_name = "Mention d'Unité"
        verbose_name_plural = "Mentions d'Unité"

    @property
    def is_valide(self):
        return (self.statut == self.StatutMention.ACTIVE and 
                self.date_echeance >= timezone.now().date() and
                self.licence.statut == Licence.Statut.VALIDE)