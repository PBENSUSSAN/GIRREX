# Fichier : competences/models/licence.py

from django.db import models
from core.models import Agent

class Licence(models.Model):
    """
    Modèle central représentant l'autorisation globale d'un contrôleur.
    Il est le pivot pour l'aptitude médicale (via l'Agent) et linguistique.
    """
    class Statut(models.TextChoices):
        VALIDE = 'VALIDE', 'Valide'
        INAPTE_TEMPORAIRE = 'INAPTE_TEMP', 'Inapte Temporaire'
        INAPTE_DEFINITIVE = 'INAPTE_DEF', 'Inapte Définitive'
        SUSPENDUE = 'SUSPENDUE', 'Suspendue'

    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='licence')
    numero_licence = models.CharField(max_length=100, unique=True, verbose_name="N° Licence / Brevet")
    date_delivrance = models.DateField()
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.VALIDE)
    
    motif_inaptitude = models.TextField(blank=True, null=True, help_text="Raison de l'inaptitude ou de la suspension.")
    date_debut_inaptitude = models.DateField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Licence de contrôleur"
        verbose_name_plural = "Licences des contrôleurs"
        permissions = [
            ('view_all_licences', 'Peut voir les dossiers de compétences de tous les agents'),
            ('view_centre_licences', 'Peut voir les dossiers de compétences des agents de son centre'),
        ]

    def __str__(self):
        return f"Licence de {self.agent.trigram or self.agent.reference}"

class MentionLinguistique(models.Model):
    """ Suivi de la compétence linguistique d'un agent. """
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name='mentions_linguistiques')
    langue = models.CharField(max_length=20, choices=[('ANGLAIS', 'Anglais'), ('FRANCAIS', 'Français')])
    niveau_oaci = models.IntegerField(choices=[(4, 'Niveau 4'), (5, 'Niveau 5'), (6, 'Niveau 6')])
    date_evaluation = models.DateField()
    date_echeance = models.DateField()
    
    class Meta:
        verbose_name = "Mention Linguistique"
        verbose_name_plural = "Mentions Linguistiques"
        unique_together = ('licence', 'langue')

class FormationReglementaire(models.Model):
    """ Catalogue des formations réglementaires obligatoires. """
    nom = models.CharField(max_length=100, unique=True) # Ex: "Facteurs Humains RAF Aéro"
    periodicite_ans = models.PositiveIntegerField(default=3, verbose_name="Périodicité (en années)")

    class Meta:
        verbose_name = "Formation Réglementaire"
        verbose_name_plural = "Formations Réglementaires"

    def __str__(self):
        return self.nom

class SuiviFormationReglementaire(models.Model):
    """ Table de liaison pour tracer quand un agent a suivi une formation. """
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name='formations_suivies')
    formation = models.ForeignKey(FormationReglementaire, on_delete=models.CASCADE)
    date_realisation = models.DateField()
    date_echeance = models.DateField()

    class Meta:
        verbose_name = "Suivi de Formation Réglementaire"
        verbose_name_plural = "Suivis des Formations Réglementaires"