# Fichier : feedback/models.py

from django.db import models
from core.models import Agent
from django.contrib.contenttypes.fields import GenericRelation

class Feedback(models.Model):
    class Categorie(models.TextChoices):
        BUG = 'BUG', 'Anomalie / Bug'
        AMELIORATION = 'AMELIORATION', "Suggestion d'amélioration"
        QUESTION = 'QUESTION', 'Question'
        AUTRE = 'AUTRE', 'Autre'

    class ModuleApp(models.TextChoices):
        GENERAL = 'GENERAL', 'Général / Authentification'
        PLANNING = 'PLANNING', 'Tour de Service (Planning)'
        FEUILLE_TEMPS = 'FEUILLE_TEMPS', 'Feuille de Temps'
        CAHIER_DE_MARCHE = 'CAHIER_DE_MARCHE', 'Cahier de Marche'
        DOCUMENTATION = 'DOCUMENTATION', 'Documentation'
        TECHNIQUE = 'TECHNIQUE', 'Technique (Pannes & MISO)'
        QS = 'QS', 'Sécurité Aérienne (QS)'
        ES = 'ES', 'Études de Sécurité (ES)'
        CYBER = 'CYBER', 'Cybersécurité (SMSI)'
        SUIVI = 'SUIVI', 'Suivi des Actions'
        FEEDBACK = 'FEEDBACK', 'Module de Feedback' # Le module peut se référencer lui-même

    titre = models.CharField(max_length=255)
    description = models.TextField()
    categorie = models.CharField(max_length=20, choices=Categorie.choices)
    module_concerne = models.CharField(max_length=30, choices=ModuleApp.choices, verbose_name="Module Concerné")
    
    auteur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='feedbacks_soumis')
    created_at = models.DateTimeField(auto_now_add=True)

    # Le seul point de contact avec le module de suivi
    action_suivi = GenericRelation('suivi.Action')

    class Meta:
        verbose_name = "Retour Utilisateur"
        verbose_name_plural = "Retours Utilisateurs"
        ordering = ['-created_at']
        permissions = [
            ('view_feedback_dashboard', 'Peut voir le tableau de bord des feedbacks'),
        ]

    def __str__(self):
        return self.titre