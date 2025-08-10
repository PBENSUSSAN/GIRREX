# Fichier : documentation/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import Agent, Centre
from datetime import timedelta

class DocumentType(models.Model):
    """ Modèle inchangé, définit les catégories de documents (Manuel, Procédure...). """
    nom = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Type de Document"
        verbose_name_plural = "Types de Documents"

    def __str__(self):
        return self.nom

class Document(models.Model):
    """
    Modèle unique représentant un document identifiable avec son cycle de vie,
    son contenu physique, et ses relations (remplacement, avenant).
    """
    
    class Statut(models.TextChoices):
        EN_REDACTION = 'EN_REDACTION', 'En Rédaction'
        EN_VIGUEUR = 'EN_VIGUEUR', 'En Vigueur'
        REMPLACE = 'REMPLACE', 'Remplacé'
        ARCHIVE = 'ARCHIVE', 'Archivé'

    # --- Champs d'Identification ---
    reference = models.CharField(max_length=100, unique=True)
    intitule = models.CharField(max_length=255, verbose_name="Intitulé")
    type_document = models.ForeignKey(DocumentType, on_delete=models.PROTECT, verbose_name="Type de document")
    description = models.TextField(blank=True, verbose_name="Objet du document")
    
    # --- Contenu Physique ---
    fichier_pdf = models.FileField(upload_to='documentation/%Y/%m/', help_text="Le fichier PDF associé à ce document.")

    # --- Périmètre & Responsabilité ---
    centres_applicables = models.ManyToManyField(Centre, blank=True, related_name='documentation_applicable')
    responsable_suivi = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='documents_supervises', verbose_name="Responsable du suivi")

    # --- Cycle de Vie & Surveillance ---
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_REDACTION)
    date_mise_en_vigueur = models.DateField(null=True, blank=True, help_text="Date à partir de laquelle le document est applicable.")
    periodicite_relecture_mois = models.PositiveIntegerField(default=12, verbose_name="Périodicité de relecture (en mois)", help_text="Ex: 12 pour une relecture annuelle.")
    date_prochaine_echeance = models.DateField(null=True, blank=True, verbose_name="Prochaine échéance de relecture")

    # --- Relations (Versions et Avenants) ---
    remplace_document = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='remplace_par', help_text="Le document que cette version remplace.")
    document_parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='avenants', help_text="Le document principal auquel cet avenant est rattaché.")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Logique de calcul automatique de la prochaine échéance
        if self.date_mise_en_vigueur:
            self.date_prochaine_echeance = self.date_mise_en_vigueur + timedelta(days=30.44 * self.periodicite_relecture_mois)
        
        # Logique pour mettre à jour le statut de l'ancien document
        if self.pk is None and self.remplace_document: # Uniquement à la création
            ancien_document = self.remplace_document
            if ancien_document.statut == self.Statut.EN_VIGUEUR:
                ancien_document.statut = self.Statut.REMPLACE
                ancien_document.save()
                
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} - {self.intitule}"