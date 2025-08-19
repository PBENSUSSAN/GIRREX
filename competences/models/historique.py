# Dans competences/models/licence.py ou un nouveau fichier competences/models/historique.py

from django.db import models 
from .licence import Licence


class HistoriqueCompetence(models.Model):
    class TypeEvenement(models.TextChoices):
        STATUT_LICENCE_CHANGE = 'STATUT_LICENCE', 'Changement Statut Licence'
        MENTION_EXPIREE = 'MENTION_EXPIREE', 'Mention d\'Unité Expirée'
        FORMATION_ECHOUE = 'FORMATION_ECHOUE', 'Formation Réglementaire Échue'
        APTITUDE_MEDICALE_EXPIREE = 'APTITUDE_MEDICALE_EXPIREE', 'Aptitude Médicale Expirée'
        APTITUDE_LINGUISTIQUE_EXPIREE = 'APTITUDE_LINGUISTIQUE_EXPIREE', 'Aptitude Linguistique Expirée'

    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name='historique')
    timestamp = models.DateTimeField(auto_now_add=True)
    type_evenement = models.CharField(max_length=40, choices=TypeEvenement.choices)
    details = models.JSONField(help_text="Détails sur l'événement : quelle mention, quelle échéance, etc.")
    
    class Meta:
        verbose_name = "Historique de Compétence"
        verbose_name_plural = "Historiques des Compétences"
        ordering = ['-timestamp']