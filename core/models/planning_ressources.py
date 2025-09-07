# Fichier : core/models/planning_ressources.py

from django.db import models
from .rh import Centre

class IndisponibiliteCabine(models.Model):
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name='indisponibilites_cabines')
    nom_cabine = models.CharField(max_length=100, help_text="Ex: 'Cabine 1', 'Position TOUR'")
    date_jour = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    motif = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Indisponibilité de Cabine"
        verbose_name_plural = "Indisponibilités de Cabines"

class TypeActiviteHorsVol(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    couleur_affichage = models.CharField(max_length=7, default='#CCCCCC', help_text="Code couleur Hex (ex: #CCCCCC)")

    def __str__(self):
        return self.nom