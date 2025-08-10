# Fichier : documentation/admin.py

from django.contrib import admin
# On importe uniquement les modèles qui existent encore : DocumentType et Document
from .models import DocumentType, Document

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """ Interface d'administration pour les Types de Document. """
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """ Interface d'administration pour le nouveau modèle Document unifié. """
    list_display = (
        'reference', 
        'intitule', 
        'type_document', 
        'statut', 
        'responsable_suivi', 
        'date_mise_en_vigueur',
        'date_prochaine_echeance'
    )
    list_filter = ('statut', 'type_document', 'centres_applicables', 'responsable_suivi')
    search_fields = ('reference', 'intitule', 'description')
    ordering = ('-created_at',)
    
    autocomplete_fields = ['responsable_suivi', 'remplace_document', 'document_parent']
    filter_horizontal = ('centres_applicables',)
    readonly_fields = ('date_prochaine_echeance',)

# Les anciennes classes VersionDocumentAdmin et RelectureAdmin ont été supprimées.