# Fichier : competences/models/brevet.py

from django.db import models
from core.models import Agent

class Brevet(models.Model):
    """
    Représente le diplôme initial, unique et permanent d'un agent contrôleur.
    C'est le "sésame" acquis à vie.
    """
    agent = models.OneToOneField(
        Agent, 
        on_delete=models.CASCADE, 
        related_name='brevet'
    )
    numero_brevet = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Numéro de Brevet"
    )
    date_delivrance = models.DateField()

    class Meta:
        verbose_name = "Brevet de contrôleur"
        verbose_name_plural = "Brevets des contrôleurs"
        permissions = [
            ('view_all_brevets', 'Peut voir les dossiers de compétences de tous les agents'),
            ('view_centre_brevets', 'Peut voir les dossiers de compétences des agents de son centre'),
        ]

    def __str__(self):
        return f"Brevet de {self.agent.trigram or self.agent.reference}"