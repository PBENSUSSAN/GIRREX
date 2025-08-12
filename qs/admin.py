# Fichier : qs/admin.py

from django.contrib import admin
# On importe uniquement les modèles qui existent réellement dans notre nouveau qs/models.py
from .models import DossierEvenement, FNE, RecommendationQS

@admin.register(DossierEvenement)
class DossierEvenementAdmin(admin.ModelAdmin):
    list_display = ('id_girrex', 'titre', 'date_evenement', 'statut_global')
    search_fields = ('id_girrex', 'titre')
    list_filter = ('statut_global', 'date_evenement')

@admin.register(FNE)
class FNEAdmin(admin.ModelAdmin):
    list_display = ('numero_oasis', 'centre', 'type_evenement', 'statut_fne', 'echeance_cloture')
    search_fields = ('numero_oasis', 'dossier__titre')
    list_filter = ('statut_fne', 'type_evenement', 'centre', 'presente_en_cdsa_cmsa')
    autocomplete_fields = ['dossier', 'agent_implique']

@admin.register(RecommendationQS)
class RecommendationQSAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'source', 'statut', 'responsable', 'date_echeance')
    list_filter = ('statut',)
    search_fields = ('description',)
    autocomplete_fields = ['responsable']