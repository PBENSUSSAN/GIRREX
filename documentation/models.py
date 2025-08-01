# Fichier : documentation/models.py (Version finale intégrant le suivi du renouvellement)

from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import Agent, Centre
from datetime import timedelta
from suivi.models import Action


# ==============================================================================
# Modèle DocumentType : Inchangé
# ==============================================================================
class DocumentType(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Type de Document"
        verbose_name_plural = "Types de Documents"

    def __str__(self):
        return self.nom

# ==============================================================================
# Modèle Document : Le chef d'orchestre du cycle de vie
# ==============================================================================
class Document(models.Model):
    class StatutSuivi(models.TextChoices):
        A_JOUR = 'A_JOUR', 'À jour'
        RENOUVELLEMENT_PLANIFIE = 'RENOUVELLEMENT_PLANIFIE', 'Renouvellement planifié'
        EN_REDACTION = 'EN_REDACTION', 'En rédaction (Nouvelle version)'
        PERIME = 'PERIME', 'Périmé (Action requise)'
        ARCHIVE = 'ARCHIVE', 'Archivé'

    intitule = models.CharField(max_length=255, verbose_name="Intitulé")
    reference = models.CharField(max_length=100, unique=True)
    type_document = models.ForeignKey(DocumentType, on_delete=models.PROTECT, verbose_name="Type de document")
    description = models.TextField(blank=True, verbose_name="Objet du document")
    
    statut_suivi = models.CharField(max_length=30, choices=StatutSuivi.choices, default=StatutSuivi.A_JOUR)
    
    responsable_suivi = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='documents_supervises', verbose_name="Responsable du suivi", null=True, blank=True)
    
    date_echeance_suivi = models.DateField(verbose_name="Prochaine échéance (relecture/remplacement)",null=True, blank=True)
    
    centres_applicables = models.ManyToManyField(Centre, blank=True, related_name='documentation_applicable')

    class Meta:
        verbose_name = "Fiche Document"
        verbose_name_plural = "Fiches Document"
        ordering = ['reference']

    def __str__(self):
        return f"{self.reference} - {self.intitule}"

# ==============================================================================
# Modèle VersionDocument : Le conteneur du fichier PDF
# ==============================================================================
class VersionDocument(models.Model):
    class StatutVersion(models.TextChoices):
        EN_VIGUEUR = 'EN_VIGUEUR', 'En vigueur'
        REMPLACEE = 'REMPLACEE', 'Remplacée'
        ARCHIVEE = 'ARCHIVEE', 'Archivée'

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    numero_version = models.CharField(max_length=20)
    fichier_pdf = models.FileField(upload_to='documentation/%Y/%m/', help_text="Le fichier PDF finalisé")
    date_mise_en_vigueur = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=StatutVersion.choices, default=StatutVersion.EN_VIGUEUR)
    commentaire_version = models.TextField(blank=True, help_text="Résumé des modifications")
    
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    enregistre_le = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        # On intercepte notre signal avant l'initialisation
        self._creation_manuelle = kwargs.pop('_creation_manuelle', False)
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        est_une_creation = self._state.adding
        super().save(*args, **kwargs)

        # L'action automatique ne se déclenche que si c'est une création
        # ET si elle ne vient pas du processus manuel.
        if est_une_creation and not self._creation_manuelle:
            responsable = self.document.responsable_suivi
            if responsable:
                Action.objects.create(
                    titre=f"Diffuser la v{self.numero_version} du document '{self.document.reference}'",
                    responsable=responsable,
                    echeance=timezone.now().date() + timedelta(days=14),
                    objet_source=self,
                    description="Veuillez lancer la diffusion de cette nouvelle version documentaire.",
                    categorie=Action.CategorieAction.DIFFUSION_DOC
                )

    class Meta:
        verbose_name = "Version de Document"
        verbose_name_plural = "Versions de Document"
        ordering = ['-date_mise_en_vigueur']
        unique_together = ('document', 'numero_version')

    def __str__(self):
        return f"Version {self.numero_version} de {self.document.reference}"

# ==============================================================================
# Modèle Relecture : Reste pertinent pour tracer les relectures
# ==============================================================================
class Relecture(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='historique_relectures')
    version_concernee = models.ForeignKey(VersionDocument, on_delete=models.PROTECT)
    date_realisation = models.DateField(default=timezone.now)
    realisee_par = models.ForeignKey(Agent, on_delete=models.PROTECT)
    decision = models.CharField(max_length=255, help_text="Ex: 'Document reconduit sans modification'")
    
    class Meta:
        verbose_name = "Historique de Relecture"
        verbose_name_plural = "Historiques de Relecture"
        ordering = ['-date_realisation']