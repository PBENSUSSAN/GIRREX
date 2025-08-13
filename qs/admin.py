# Fichier : qs/admin.py

from django.contrib import admin
from .models import FNE, RecommendationQS, RapportExterne # Mise à jour des imports

@admin.register(FNE)
class FNEAdmin(admin.ModelAdmin):
    # On ajoute les nouveaux champs pour un meilleur affichage
    list_display = ('id_girrex', 'titre', 'numero_oasis', 'centre', 'statut_fne', 'echeance_cloture')
    search_fields = ('id_girrex', 'titre', 'numero_oasis')
    list_filter = ('statut_fne', 'type_evenement', 'centre', 'presente_en_cdsa_cmsa')
    autocomplete_fields = ['agent_implique']

@admin.register(RecommendationQS)
class RecommendationQSAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'source', 'statut', 'responsable', 'date_echeance')
    list_filter = ('statut',)
    search_fields = ('description',)
    autocomplete_fields = ['responsable']

# On ajoute l'admin pour RapportExterne pour pouvoir le consulter
@admin.register(RapportExterne)
class RapportExterneAdmin(admin.ModelAdmin):
    list_display = ('organisme_source', 'reference_externe', 'date_reception', 'fne')
    autocomplete_fields = ['fne']