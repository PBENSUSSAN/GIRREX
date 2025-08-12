# ==============================================================================
# Fichier : core/models/qualite.py
# Modèles de données pour la gestion de la Qualité / Sécurité des Vols (QS/SMS).
# ==============================================================================

from django.db import models
from core.models import Agent, Centre, Formation
from documentation.models import Document


# ==============================================================================
# SECTION VI : QUALITE/SECURITE DES VOLS (QS/SMS)
# ==============================================================================

class ResponsableQSCentral(models.Model):
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='responsabilite_qs_central')
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Responsable QS Central"
        verbose_name_plural = "Responsables QS Central"

    def __str__(self):
        return f"Responsabilité QS Centrale de {self.agent}"

class EvenementQS(models.Model):
    STATUT_CHOICES = [('ouvert', 'Ouvert'), ('analyse', 'En analyse'), ('clos', 'Clos')]
    
    date_evenement = models.DateField()
    type_evenement = models.CharField(max_length=100)
    description = models.TextField()
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT)
    rapporteur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='evenements_rapportes_qs')
    niveau_gravite = models.CharField(max_length=50, help_text="Ex: Mineur, Significatif, Majeur")
    analyse = models.TextField(blank=True, help_text="Analyse à froid de l'événement")
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='ouvert')
    
    class Meta:
        verbose_name = "Événement QS"
        verbose_name_plural = "Événements QS"

    def __str__(self):
        return f"Événement du {self.date_evenement}: {self.type_evenement}"

class RecommendationQS(models.Model):
    STATUT_CHOICES = [
        ('proposee', 'Proposée'), 
        ('acceptee', 'Acceptée'), 
        ('refusee', 'Refusée'), 
        ('implementee', 'Implémentée')
    ]
    
    evenement = models.ForeignKey(EvenementQS, on_delete=models.CASCADE, related_name='recommandations')
    description = models.TextField()
    priorite = models.CharField(max_length=50, help_text="Ex: Haute, Moyenne, Basse")
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='proposee')
    date_emission = models.DateField(auto_now_add=True)
    date_echeance = models.DateField()
    responsable = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='recommandations_qs_responsable')
    diffusion_nationale = models.BooleanField(default=False)
    centres_cibles = models.ManyToManyField(Centre, blank=True, related_name='recommandations_qs_cibles')
    
    class Meta:
        verbose_name = "Recommandation QS"
        verbose_name_plural = "Recommandations QS"

    def __str__(self):
        return f"Reco: {self.description[:80]}"

class ActionQS(models.Model):
    STATUT_CHOICES = [('a_faire', 'À faire'), ('en_cours', 'En cours'), ('fait', 'Fait'), ('annule', 'Annulé')]
    
    recommendation = models.ForeignKey(RecommendationQS, on_delete=models.CASCADE, related_name='actions_qs')
    description = models.TextField()
    date_prevue = models.DateField()
    date_realisation = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_faire')
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, help_text="Lien vers une formation si l'action en est une")
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, help_text="Lien vers un document si l'action est documentaire")
    archive = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Action QS"
        verbose_name_plural = "Actions QS"

    def __str__(self):
        return f"Action QS: {self.description[:80]}"

class AuditQS(models.Model):
    auditeur = models.ForeignKey(Agent, on_delete=models.PROTECT)
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='audits_recus')
    date_audit = models.DateField()
    type_audit = models.CharField(max_length=100)
    rapport = models.TextField(blank=True, help_text="Résumé du rapport d'audit")
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, help_text="Lien vers le rapport d'audit complet")
    
    class Meta:
        verbose_name = "Audit QS"
        verbose_name_plural = "Audits QS"

class EvaluationRisqueQS(models.Model):
    STATUT_CHOICES = [('identifie', 'Identifié'), ('evalue', 'Évalué'), ('maitrise', 'Maîtrisé'), ('clos', 'Clos')]
    
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT)
    date_evaluation = models.DateField()
    description = models.TextField()
    niveau_risque = models.CharField(max_length=50, help_text="Ex: Acceptable, Tolérable, Inacceptable")
    recommandations = models.TextField(blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='identifie')
    
    class Meta:
        verbose_name = "Évaluation de Risque QS"
        verbose_name_plural = "Évaluations de Risques QS"

class NotificationQS(models.Model):
    STATUT_CHOICES = [('a_envoyer', 'À envoyer'), ('envoye', 'Envoyé'), ('erreur', 'Erreur')]
    
    action = models.ForeignKey(ActionQS, on_delete=models.CASCADE, related_name='notifications_qs')
    destinataire = models.CharField(max_length=255)
    date_envoi = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_envoyer')
    message = models.TextField()
    
    class Meta:
        verbose_name = "Notification QS"
        verbose_name_plural = "Notifications QS"