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
# 1. NOUVEAU MODÈLE : LE DOSSIER D'ÉVÉNEMENT (CHAPEAU)
# ==============================================================================
class DossierEvenement(models.Model):
    """
    Objet "chapeau" qui regroupe toutes les FNE liées à un même incident.
    """
    class Statut(models.TextChoices):
        OUVERT = 'OUVERT', 'Ouvert'
        CLOTURE = 'CLOTURE', 'Clôturé'

    id_girrex = models.CharField(max_length=50, unique=True, verbose_name="ID Girrex")
    titre = models.CharField(max_length=255, verbose_name="Titre de l'événement")
    date_evenement = models.DateField()
    statut_global = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT)
    description_detaillee = models.TextField(blank=True, verbose_name="Analyse globale (QS National)")

    class Meta:
        verbose_name = "Dossier d'Événement"
        verbose_name_plural = "Dossiers d'Événement"
        ordering = ['-date_evenement']

    def __str__(self):
        return f"{self.id_girrex} - {self.titre}"

# ==============================================================================
# 2. MODÈLE ADAPTÉ : LA FICHE DE NOTIFICATION D'ÉVÉNEMENT (FNE)
# ==============================================================================
class FNE(models.Model):
    """
    Représente le dossier d'instruction local pour un centre, lié à une déclaration OASIS.
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

    dossier = models.ForeignKey(DossierEvenement, on_delete=models.CASCADE, related_name='fne_liees')
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
        return self.numero_oasis or f"FNE non déclarée pour {self.centre.code_centre}"

# ==============================================================================
# 3. MODÈLE ADAPTÉ : LA RECOMMANDATION QS
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

# ==============================================================================
# 3. MODÈLE ADAPTÉ : RAPPORT EXTERNE
# ==============================================================================

class RapportExterne(models.Model):
    dossier = models.ForeignKey(DossierEvenement, on_delete=models.CASCADE, related_name='rapports_externes')
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
# 4. MODÈLE POUR LE JOURNAL D'AUDIT PERMANENT
# ==============================================================================
class HistoriqueFNE(models.Model):
    """
    Journal d'audit pérenne des événements importants survenus
    pendant l'instruction d'une Fiche de Notification d'Événement (FNE).
    """
    class TypeEvenement(models.TextChoices):
        CREATION = 'CREATION', "Création du processus d'instruction"
        DECLARATION_OASIS = 'DECLARATION_OASIS', "Déclaration OASIS effectuée"
        COMMENTAIRE = 'COMMENTAIRE', 'Commentaire ajouté'
        CHANGEMENT_STATUT_INSTRUCTION = 'CHANGEMENT_STATUT_INSTRUCTION', "Changement d'état de l'instruction"
        CLOTURE = 'CLOTURE', 'Clôture de la FNE'

    fne = models.ForeignKey(
        FNE, 
        on_delete=models.CASCADE, 
        related_name='historique_permanent' # Nom de relation explicite
    )
    timestamp = models.DateTimeField(
        help_text="Date et heure effectives de l'événement."
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        help_text="Utilisateur à l'origine de l'événement."
    )
    type_evenement = models.CharField(
        max_length=40, # Augmenté pour correspondre à la nouvelle valeur
        choices=TypeEvenement.choices
    )
    details = models.JSONField(
        default=dict,
        help_text="Données contextuelles de l'événement (ex: le commentaire, l'ancien/nouveau statut)."
    )

    class Meta:
        verbose_name = "Historique Permanent FNE"
        verbose_name_plural = "Historiques Permanents FNE"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit FNE #{self.fne_id} - {self.get_type_evenement_display()}"
