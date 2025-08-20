# Fichier : competences/models/formation.py

from django.db import models
from core.models import Agent
from .brevet import Brevet

class MentionLinguistique(models.Model):
    """ Suivi de la compétence linguistique d'un agent. Lié au Brevet. """
    brevet = models.ForeignKey(
        Brevet, 
        on_delete=models.CASCADE, 
        related_name='mentions_linguistiques'
    )
    langue = models.CharField(
        max_length=20, 
        choices=[('ANGLAIS', 'Anglais'), ('FRANCAIS', 'Français')]
    )
    niveau_oaci = models.IntegerField(
        choices=[(4, 'Niveau 4'), (5, 'Niveau 5'), (6, 'Niveau 6')]
    )
    date_evaluation = models.DateField()
    date_echeance = models.DateField()
    
    class Meta:
        verbose_name = "Mention Linguistique"
        verbose_name_plural = "Mentions Linguistiques"
        unique_together = ('brevet', 'langue')

class FormationReglementaire(models.Model):
    """ Catalogue des formations réglementaires obligatoires (ex: RAF AERO). """
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom complet")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Identifiant unique")
    periodicite_ans = models.PositiveIntegerField(default=3, verbose_name="Périodicité (ans)")

    def __str__(self):
        return self.nom

class SuiviFormationReglementaire(models.Model):
    """ Trace le suivi d'une formation réglementaire par un agent. """
    brevet = models.ForeignKey(
        Brevet, 
        on_delete=models.CASCADE, 
        related_name='formations_reglementaires_suivies'
    )
    formation = models.ForeignKey(FormationReglementaire, on_delete=models.CASCADE)
    date_realisation = models.DateField()
    date_echeance = models.DateField()

class SuiviFormationContinue(models.Model):
    """ Trace le suivi des formations continues (PCU, FSAU). """
    class TypeFormation(models.TextChoices):
        PCU = 'PCU', 'PCU'
        FSAU = 'FSAU', 'FSAU'

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='formations_continues_suivies')
    type_formation = models.CharField(max_length=4, choices=TypeFormation.choices)
    date_realisation = models.DateField()

    class Meta:
        verbose_name = "Suivi de Formation Continue"
        verbose_name_plural = "Suivis de Formation Continue"
        ordering = ['-date_realisation']