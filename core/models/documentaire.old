# ==============================================================================
# Fichier : core/models/documentaire.py
# Modèles de données pour la gestion documentaire.
# ==============================================================================

from django.db import models
from .rh import Agent, Centre  # Import relatif depuis le fichier rh.py du même paquet

# ==============================================================================
# SECTION IV : GESTION DOCUMENTAIRE
# ==============================================================================

class DocumentType(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Type de Document"
        verbose_name_plural = "Types de Documents"

    def __str__(self):
        return self.nom

class Document(models.Model):
    type_document = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    fichier = models.FileField(
        upload_to='documents/current/%Y/%m/', 
        blank=True, 
        help_text="Fichier de la version actuellement en vigueur"
    )
    reference = models.CharField(max_length=100, unique=True)
    date_creation = models.DateField(auto_now_add=True)
    date_mise_a_jour = models.DateField(auto_now=True)
    est_archive = models.BooleanField(default=False)
    responsable_sms = models.ForeignKey(
        Agent, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='documents_sous_responsabilite'
    )
    centres_visibles = models.ManyToManyField(
        Centre, 
        blank=True, 
        related_name='documentation_visible', 
        help_text="Centres pour qui ce document est applicable"
    )
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"{self.reference} - {self.titre}"

class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    numero_version = models.CharField(max_length=20)
    fichier = models.FileField(upload_to='documents/archives/%Y/%m/')
    date_version = models.DateField()
    commentaire = models.TextField(blank=True, help_text="Résumé des modifications apportées dans cette version")
    
    class Meta:
        verbose_name = "Version de Document"
        verbose_name_plural = "Versions de Documents"
        ordering = ['-date_version']
        unique_together = ('document', 'numero_version')

    def __str__(self):
        return f"{self.document.reference} - v{self.numero_version}"

class SignatureCircuit(models.Model):
    STATUT_CHOICES = [('en_attente', 'En attente'), ('signe', 'Signé'), ('refuse', 'Refusé')]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='circuit_signatures')
    ordre = models.PositiveIntegerField(help_text="Ordre de l'étape dans le circuit (1, 2, 3...)")
    organisme = models.CharField(max_length=255, help_text="Entité ou fonction qui doit signer (ex: Chef de centre, Responsable QS)")
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, help_text="Agent qui a effectivement signé")
    date_signature = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='en_attente')
    commentaire = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Étape de Signature"
        verbose_name_plural = "Étapes de Signature"
        ordering = ['document', 'ordre']
        unique_together = ('document', 'ordre')

    def __str__(self):
        return f"Étape {self.ordre} pour {self.document.reference}"