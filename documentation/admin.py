# Fichier : documentation/admin.py (Version corrigée et alignée sur les nouveaux modèles)

from django.contrib import admin
# On importe uniquement les modèles qui existent réellement maintenant
from .models import DocumentType, Document, VersionDocument, Relecture

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """ Interface d'administration pour les Types de Document. """
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """ Interface d'administration pour les Fiches Document. """
    # On met à jour les champs pour correspondre au nouveau modèle
    list_display = ('reference', 'intitule', 'type_document', 'statut_suivi', 'responsable_suivi', 'date_echeance_suivi')
    list_filter = ('statut_suivi', 'type_document', 'centres_applicables', 'responsable_suivi')
    search_fields = ('reference', 'intitule', 'description')
    ordering = ('reference',)
    
    # On met à jour les champs d'autocomplétion
    autocomplete_fields = ['responsable_suivi']
    
    filter_horizontal = ('centres_applicables',)

@admin.register(VersionDocument)
class VersionDocumentAdmin(admin.ModelAdmin):
    """ Interface d'administration pour les Versions de Document. """
    # On met à jour les champs pour correspondre au nouveau modèle
    list_display = ('document', 'numero_version', 'statut', 'date_mise_en_vigueur')
    list_filter = ('statut', 'document__reference')
    search_fields = ('numero_version', 'document__reference', 'commentaire_version')
    
    autocomplete_fields = ['document']
    
@admin.register(Relecture)
class RelectureAdmin(admin.ModelAdmin):
    """ Interface d'administration pour l'historique des relectures. """
    list_display = ('document', 'version_concernee', 'date_realisation', 'realisee_par', 'decision')
    list_filter = ('date_realisation', 'realisee_par')
    search_fields = ('document__reference', 'decision')
    
    autocomplete_fields = ['document', 'version_concernee', 'realisee_par']

# La classe pour EtapeSignature a été supprimée car le modèle n'existe plus.