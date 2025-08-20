# Fichier : competences/models/qualification.py

from django.db import models
from core.models import Centre
from .brevet import Brevet

class Qualification(models.Model):
    """
    Représente un jalon de carrière ou un privilège obtenu par un agent,
    dans un centre donné. C'est le "CV" de l'agent, centre par centre.
    """
    class TypeFlux(models.TextChoices):
        CAM = 'CAM', 'CAM'
        CAG_ACS = 'CAG_ACS', 'CAG - ACS'
        CAG_APS = 'CAG_APS', 'CAG - APS'
        TOUR = 'TOUR', 'Position TOUR'

    class TypeQualification(models.TextChoices):
        # Qualifications CAM
        CAER = 'CAER', 'CAER'
        PC = 'PC', 'PC'
        CDQ = 'CDQ', 'Chef de Quart'
        ISP = 'ISP', 'Instructeur sur Position'
        EXA = 'EXA', 'Examinateur'
        # Qualifications CAG
        ACS = 'ACS', 'Contrôle d\'Approche de Surveillance'
        APS = 'APS', 'Contrôle d\'Approche de Précision'
        ADI = 'ADI', 'Contrôle d\'Aérodrome aux Instruments'
        ADV = 'ADV', 'Contrôle d\'Aérodrome à Vue'

    class Statut(models.TextChoices):
        ACTIF = 'ACTIF', 'Actif'
        ARCHIVE_MUTATION = 'ARCHIVE_MUTATION', 'Archivé (suite à mutation)'

    brevet = models.ForeignKey(
        Brevet, 
        on_delete=models.CASCADE, 
        related_name='qualifications'
    )
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name='qualifications_delivrees'
    )
    type_flux = models.CharField(
        max_length=10, 
        choices=TypeFlux.choices
    )
    type_qualification = models.CharField(
        max_length=10, 
        choices=TypeQualification.choices
    )
    date_obtention = models.DateField()
    statut = models.CharField(
        max_length=20, 
        choices=Statut.choices, 
        default=Statut.ACTIF
    )

    class Meta:
        verbose_name = "Qualification / Privilège"
        verbose_name_plural = "Qualifications & Privilèges"
        ordering = ['brevet', 'centre', 'date_obtention']
        unique_together = ('brevet', 'centre', 'type_qualification')

    def __str__(self):
        return f"{self.get_type_qualification_display()} pour {self.brevet.agent.trigram} à {self.centre.code_centre}"