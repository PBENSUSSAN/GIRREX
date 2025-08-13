# Fichier : qs/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# On importe les modèles des autres applications avec lesquels on a des relations
from core.models import Agent, Centre, Formation
from documentation.models import Document
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# ==============================================================================
# MODÈLE FNE (FINAL)
# ==============================================================================
class FNE(models.Model):
    """
    Représente le dossier d'instruction pour un événement de sécurité.
    C'est maintenant l'objet central.
    """
    class StatutFNE(models.TextChoices):
        PRE_DECLAREE = 'PRE_DECLAREE', 'Pré-déclarée (en attente OASIS)'
        EN_ATTENTE_INSTRUCTION = 'ATTENTE_INSTRUCTION', "En attente d'instruction"
        INSTRUCTION_EN_COURS = 'INSTRUCTION_COURS', 'Instruction en cours'
        ATTENTE_PROLONGATION = 'ATTENTE_PROLONGATION', 'En attente de prolongation'
        CLOTUREE = 'CLOTUREE', 'Clôturée'
        CLOTUREE_PROLONGATION = 'CLOTUREE_PROLONGATION', 'Clôturée (avec prolongation)'

    class TypeEvenement(models.TextChoices):
        ATM = 'ATM', 'ATM (Air Traffic Management)'
        TECHNIQUE = 'TECHNIQUE', 'Technique'
        AUTRE = 'AUTRE', 'Autre'

    class TypeCloture(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard'
        CLS = 'CLS', 'Commission Locale de Sécurité'
        CLM = 'CLM', 'Commission Locale Mixte'

    # --- Champs anciennement dans DossierEvenement (maintenant obligatoires) ---
    id_girrex = models.CharField(max_length=50, unique=True, verbose_name="ID Girrex de l'Événement")
    titre = models.CharField(max_length=255, verbose_name="Titre de l'événement")
    date_evenement = models.DateField()
    description_globale = models.TextField(blank=True, verbose_name="Analyse globale (QS National)")
    
    # --- Champs originaux de FNE ---
    numero_oasis = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="Numéro OASIS")
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='fne')
    agent_implique = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='fne_implique')
    type_evenement = models.CharField(max_length=20, choices=TypeEvenement.choices, default=TypeEvenement.AUTRE)
    statut_fne = models.CharField(max_length=30, choices=StatutFNE.choices, default=StatutFNE.PRE_DECLAREE)
    
    date_declaration_oasis = models.DateField(null=True, blank=True)
    echeance_cloture = models.DateField(null=True, blank=True)
    
    classification_gravite_atm = models.CharField(max_length=100, blank=True)
    classification_gravite_ats = models.CharField(max_length=100, blank=True)
    classification_probabilite = models.CharField(max_length=100, blank=True)
    
    rapport_cloture_pdf = models.FileField(upload_to='qs/rapports_cloture/%Y/%m/', blank=True, null=True)
    presente_en_cdsa_cmsa = models.BooleanField(default=False, verbose_name="Présenté en CDSA/CMSA")
    type_cloture = models.CharField(max_length=20, choices=TypeCloture.choices, default=TypeCloture.STANDARD)
    
    date_demande_prolongation = models.DateField(null=True, blank=True)
    motif_prolongation = models.TextField(blank=True)
    nouvelle_echeance = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Fiche de Notification d'Événement (FNE)"
        verbose_name_plural = "Fiches de Notification d'Événement (FNE)"
        ordering = ['-echeance_cloture']

    def save(self, *args, **kwargs):
        if self.date_declaration_oasis and not self.echeance_cloture:
            self.echeance_cloture = self.date_declaration_oasis + timedelta(days=87)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre or self.numero_oasis or f"FNE #{self.id}"

# ==============================================================================
# MODÈLE RAPPORT EXTERNE (FINAL)
# ==============================================================================
class RapportExterne(models.Model):
    fne = models.ForeignKey(FNE, on_delete=models.CASCADE, related_name='rapports_externes')
    organisme_source = models.CharField(max_length=255, verbose_name="Organisme Source")
    reference_externe = models.CharField(max_length=255, blank=True, verbose_name="Référence externe")
    description = models.TextField(verbose_name="Description")
    fichier_joint = models.FileField(upload_to='qs/rapports_externes/%Y/%m/', blank=True, null=True)
    date_reception = models.DateField()
    class Meta:
        verbose_name = "Rapport Externe"
        verbose_name_plural = "Rapports Externes"
        ordering = ['-date_reception']
    def __str__(self):
        return f"Rapport de {self.organisme_source} ({self.reference_externe})"

# ==============================================================================
# MODÈLES RECOMMANDATION ET HISTORIQUE (INCHANGÉS)
# ==============================================================================
class RecommendationQS(models.Model):
    class Statut(models.TextChoices):
        PROPOSEE = 'PROPOSEE', 'Proposée'
        ACCEPTEE = 'ACCEPTEE', 'Acceptée'
        REFUSEE = 'REFUSEE', 'Refusée'
        IMPLEMENTEE = 'IMPLEMENTEE', 'Implémentée'

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    source = GenericForeignKey('content_type', 'object_id')
    
    description = models.TextField()
    priorite = models.CharField(max_length=50, help_text="Ex: Haute, Moyenne, Basse")
    statut = models.CharField(max_length=50, choices=Statut.choices, default=Statut.PROPOSEE)
    date_emission = models.DateField(auto_now_add=True)
    date_echeance = models.DateField()
    responsable = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='recommandations_qs_responsable')
    
    destinataires_centres = models.ManyToManyField(Centre, blank=True)
    destinataires_agents = models.ManyToManyField(Agent, blank=True)
    destinataires_externes = models.TextField(blank=True, help_text="Liste d'emails séparés par des virgules")

    class Meta:
        verbose_name = "Recommandation QS"
        verbose_name_plural = "Recommandations QS"

    def __str__(self):
        return f"Reco: {self.description[:80]}"

class HistoriqueFNE(models.Model):
    class TypeEvenement(models.TextChoices):
        CREATION = 'CREATION', "Création du processus d'instruction"
        DECLARATION_OASIS = 'DECLARATION_OASIS', "Déclaration OASIS effectuée"
        COMMENTAIRE = 'COMMENTAIRE', 'Commentaire ajouté'
        CHANGEMENT_STATUT_INSTRUCTION = 'CHANGEMENT_STATUT_INSTRUCTION', "Changement d'état de l'instruction"
        CLOTURE = 'CLOTURE', 'Clôture de la FNE'

    fne = models.ForeignKey(FNE, on_delete=models.CASCADE, related_name='historique_permanent')
    timestamp = models.DateTimeField(help_text="Date et heure effectives de l'événement.")
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, help_text="Utilisateur à l'origine de l'événement.")
    type_evenement = models.CharField(max_length=40, choices=TypeEvenement.choices)
    details = models.JSONField(default=dict, help_text="Données contextuelles de l'événement (ex: le commentaire, l'ancien/nouveau statut).")

    class Meta:
        verbose_name = "Historique Permanent FNE"
        verbose_name_plural = "Historiques Permanents FNE"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit FNE #{self.fne_id} - {self.get_type_evenement_display()}"