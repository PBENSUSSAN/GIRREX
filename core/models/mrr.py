# ==============================================================================
# Fichier : core/models/mrr.py
# Modèles de données pour la gestion du changement et des exigences (MRR).
# ==============================================================================

from django.db import models
from .rh import Agent, Centre  # Import relatif depuis le fichier rh.py du même paquet

# ==============================================================================
# SECTION V : GESTION DU CHANGEMENT ET MRR (MANAGEMENT OF REGULATORY REQUIREMENTS)
# ==============================================================================

class CentreRole(models.Model):
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Rôle au sein du Centre"
        verbose_name_plural = "Rôles au sein des Centres"

    def __str__(self):
        return f"{self.agent} est {self.role} à {self.centre.code_centre}"

class ResponsableSMS(models.Model):
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='responsabilite_sms')
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Responsable SMS"
        verbose_name_plural = "Responsables SMS"

    def __str__(self):
        return f"Responsabilité SMS de {self.agent}"

class MRR(models.Model):
    STATUT_CHOICES = [('ouvert', 'Ouvert'), ('en_cours', 'En cours'), ('clos', 'Clos'), ('annule', 'Annulé')]
    
    intitule = models.CharField(max_length=255)
    date_ouverture = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='ouvert')
    commentaires = models.TextField(blank=True)
    archive = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Fiche MRR"
        verbose_name_plural = "Fiches MRR"

    def __str__(self):
        return self.intitule

class MRRSignataire(models.Model):
    mrr = models.ForeignKey(MRR, on_delete=models.CASCADE, related_name='signataires')
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT)
    date_signature = models.DateField(null=True, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = ('mrr', 'agent')
        verbose_name = "Signataire MRR"
        verbose_name_plural = "Signataires MRR"
        
class MRRProgression(models.Model):
    mrr = models.ForeignKey(MRR, on_delete=models.CASCADE, related_name='progression')
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=100)
    commentaire = models.TextField()
    
    class Meta:
        verbose_name = "Progression MRR"
        verbose_name_plural = "Progressions MRR"
        ordering = ['-date']

class Changement(models.Model):
    STATUT_CHOICES = [
        ('identifie', 'Identifié'), 
        ('analyse', 'En analyse'), 
        ('approuve', 'Approuvé'), 
        ('implemente', 'Implémenté')
    ]
    
    mrr = models.ForeignKey(MRR, on_delete=models.SET_NULL, null=True, blank=True, related_name='changements')
    origine = models.TextField(help_text="Qui ou quoi est à l'origine du changement")
    description = models.TextField()
    date_creation = models.DateField(auto_now_add=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='identifie')
    responsable_sms = models.ForeignKey(ResponsableSMS, on_delete=models.PROTECT)
    impact = models.TextField(help_text="Analyse d'impact du changement")
    archive = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Demande de Changement"
        verbose_name_plural = "Demandes de Changement"
        
    def __str__(self):
        return f"Changement: {self.description[:80]}"

class Action(models.Model):
    STATUT_CHOICES = [('a_faire', 'À faire'), ('en_cours', 'En cours'), ('fait', 'Fait'), ('annule', 'Annulé')]
    
    changement = models.ForeignKey(Changement, on_delete=models.CASCADE, related_name='actions')
    numero_action = models.CharField(max_length=50, blank=True)
    type_action = models.CharField(max_length=100, blank=True, help_text="Ex: Documentaire, Formation, Technique")
    description = models.TextField()
    date_prevue = models.DateField()
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_faire')
    archive = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Action de Changement"
        verbose_name_plural = "Actions de Changement"
        
    def __str__(self):
        return self.description[:80]

class Notification(models.Model):
    STATUT_CHOICES = [('a_envoyer', 'À envoyer'), ('envoye', 'Envoyé'), ('erreur', 'Erreur')]
    
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='notifications')
    destinataire = models.CharField(max_length=255, help_text="Email ou nom de l'agent/groupe")
    date_envoi = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_envoyer')
    message = models.TextField()
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"