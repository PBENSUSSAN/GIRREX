# Fichier : competences/admin.py

from django.contrib import admin
from .models import (
    Brevet,
    Qualification,
    MentionUniteAnnuelle,
    MentionLinguistique,
    FormationReglementaire,
    SuiviFormationReglementaire,
    SuiviFormationContinue,
    EvenementCarriere,
    RegleDeRenouvellement,
)

@admin.register(Brevet)
class BrevetAdmin(admin.ModelAdmin):
    list_display = ('agent', 'numero_brevet', 'date_delivrance')
    search_fields = ('agent__trigram', 'agent__reference', 'numero_brevet')
    autocomplete_fields = ('agent',)

@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('brevet', 'centre', 'type_flux', 'type_qualification', 'date_obtention', 'statut')
    list_filter = ('centre', 'type_flux', 'type_qualification', 'statut')
    search_fields = ('brevet__agent__trigram', 'brevet__agent__reference')
    autocomplete_fields = ('brevet', 'centre')

@admin.register(MentionUniteAnnuelle)
class MuaAdmin(admin.ModelAdmin):
    list_display = ('get_agent_trigram', 'type_flux', 'date_debut_cycle', 'date_fin_cycle', 'statut')
    list_filter = ('type_flux', 'statut', 'qualification__centre')
    search_fields = ('qualification__brevet__agent__trigram',)
    autocomplete_fields = ('qualification',)

    @admin.display(description='Agent', ordering='qualification__brevet__agent__trigram')
    def get_agent_trigram(self, obj):
        return obj.qualification.brevet.agent.trigram

@admin.register(MentionLinguistique)
class MentionLinguistiqueAdmin(admin.ModelAdmin):
    list_display = ('brevet', 'langue', 'niveau_oaci', 'date_echeance')
    list_filter = ('langue', 'niveau_oaci')
    search_fields = ('brevet__agent__trigram',)
    autocomplete_fields = ('brevet',)

@admin.register(FormationReglementaire)
class FormationReglementaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug', 'periodicite_ans')
    search_fields = ('nom',)

@admin.register(SuiviFormationReglementaire)
class SuiviFormationReglementaireAdmin(admin.ModelAdmin):
    list_display = ('brevet', 'formation', 'date_realisation', 'date_echeance')
    list_filter = ('formation',)
    search_fields = ('brevet__agent__trigram',)
    autocomplete_fields = ('brevet', 'formation')

@admin.register(SuiviFormationContinue)
class SuiviFormationContinueAdmin(admin.ModelAdmin):
    list_display = ('agent', 'type_formation', 'date_realisation')
    list_filter = ('type_formation',)
    search_fields = ('agent__trigram',)
    autocomplete_fields = ('agent',)

@admin.register(EvenementCarriere)
class EvenementCarriereAdmin(admin.ModelAdmin):
    list_display = ('agent', 'type_evenement', 'date_debut', 'date_fin')
    list_filter = ('type_evenement',)
    search_fields = ('agent__trigram',)
    autocomplete_fields = ('agent',)

@admin.register(RegleDeRenouvellement)
class RegleDeRenouvellementAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 
        'seuil_heures_total', 
        'seuil_heures_cam', 
        'seuil_heures_cag_acs',
        'seuil_heures_cag_aps',
        'seuil_heures_tour'
    )
    search_fields = ('nom',)
    filter_horizontal = ('centres',)
    
    fieldsets = (
        (None, {
            'fields': ('nom', 'centres')
        }),
        ('Seuils Requis (en heures)', {
            'description': "Définissez les objectifs d'heures. Laissez un champ à 0 si non applicable.",
            'fields': (
                'seuil_heures_total', 
                'seuil_heures_cam', 
                'seuil_heures_cag_acs',
                'seuil_heures_cag_aps',
                'seuil_heures_tour'
            )
        }),
    )