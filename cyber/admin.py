# Fichier : cyber/admin.py

from django.contrib import admin
from .models import SMSI, CyberRisque, CyberIncident

@admin.register(SMSI)
class SMSIAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le dossier de conformité SMSI.
    """
    list_display = ('centre', 'relais_local')
    search_fields = ('centre__code_centre', 'relais_local__trigram')
    # autocomplete_fields rend la sélection des ForeignKeys beaucoup plus simple
    autocomplete_fields = ['centre', 'relais_local', 'manuel_management', 'programme_surete']
    list_select_related = ('centre', 'relais_local') # Optimisation des requêtes

@admin.register(CyberRisque)
class CyberRisqueAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le registre des risques cyber.
    """
    list_display = ('id', 'smsi', 'description_courte', 'statut', 'gravite', 'probabilite')
    list_filter = ('statut', 'gravite', 'probabilite', 'smsi__centre')
    search_fields = ('description', 'smsi__centre__code_centre')
    autocomplete_fields = ['smsi']
    list_select_related = ('smsi__centre',)

    def description_courte(self, obj):
        return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
    description_courte.short_description = "Description"

@admin.register(CyberIncident)
class CyberIncidentAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le registre des incidents cyber.
    """
    list_display = ('id', 'smsi', 'date', 'description_courte', 'statut', 'source_panne')
    list_filter = ('statut', 'smsi__centre')
    search_fields = ('description', 'smsi__centre__code_centre')
    date_hierarchy = 'date' # Permet de naviguer par date
    autocomplete_fields = ['smsi', 'source_panne']
    list_select_related = ('smsi__centre', 'source_panne')

    def description_courte(self, obj):
        return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
    description_courte.short_description = "Description"