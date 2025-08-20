# Fichier : activites/models/vol.py

from django.db import models
from django.core.exceptions import ValidationError
# On importe les modèles de l'application 'core'
from core.models import Agent, Centre

class Vol(models.Model):
    """
    Représente un événement de vol unique avec ses caractéristiques immuables.
    """
    class TypeFlux(models.TextChoices):
        CAM = 'CAM', 'CAM'
        CAG_ACS = 'CAG_ACS', 'CAG - ACS'
        CAG_APS = 'CAG_APS', 'CAG - APS'
        TOUR = 'TOUR', 'Position TOUR'

    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='vols')
    date_vol = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    flux = models.CharField(max_length=10, choices=TypeFlux.choices)
    indicatif = models.CharField(max_length=100, blank=True, verbose_name="Indicatif du vol")
    
    @property
    def duree(self):
        """ Calcule la durée du vol en heures (float). """
        from datetime import datetime, timedelta
        start = datetime.combine(self.date_vol, self.heure_debut)
        end = datetime.combine(self.date_vol, self.heure_fin)
        if end < start:
            end += timedelta(days=1)
        return (end - start).total_seconds() / 3600

    def __str__(self):
        return f"Vol {self.indicatif or 'N/A'} du {self.date_vol} à {self.centre.code_centre}"

class SaisieActivite(models.Model):
    """
    Trace la participation d'un agent à un vol donné, avec un rôle spécifique.
    C'est le modèle central pour le décompte des heures.
    """
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
        unique_together = ('vol', 'agent', 'role')

    def __str__(self):
        return f"{self.agent.trigram} en tant que {self.get_role_display()} sur le vol {self.vol_id}"

    def clean(self):
        """ Ajoute des règles de validation métier. """
        # ==========================================================
        #                      CORRECTION ICI
        # ==========================================================
        # On n'exécute cette validation que si le vol parent a déjà été sauvegardé
        # et a donc un ID (pk = Primary Key).
        if self.vol and self.vol.pk:
            activites_sur_vol = SaisieActivite.objects.filter(vol=self.vol)
            if self.pk: # Exclure l'instance actuelle si elle est modifiée
                activites_sur_vol = activites_sur_vol.exclude(pk=self.pk)

            roles_actifs_existants = activites_sur_vol.filter(
                role__in=[self.Role.CONTROLEUR, self.Role.STAGIAIRE]
            ).count()

            if self.role in [self.Role.CONTROLEUR, self.Role.STAGIAIRE]:
                if roles_actifs_existants > 0:
                    raise ValidationError("Un seul 'Contrôleur en Charge' ou 'Stagiaire' est autorisé par vol.")