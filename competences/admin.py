# Fichier : competences/admin.py

from django.contrib import admin
from .models import (
    Licence, Qualification, MentionUnite, 
    MentionLinguistique, FormationReglementaire, SuiviFormationReglementaire
)

@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display = ('agent', 'numero_licence', 'statut', 'date_delivrance')
    list_filter = ('statut',)
    search_fields = ('agent__trigram', 'agent__reference', 'numero_licence')
    
    # ### CORRECTION ###
    # On supprime 'certificat_medical' car il n'est plus dans le modèle Licence.
    # Il est maintenant accessible via l'admin de l'Agent.
    autocomplete_fields = ('agent',)

@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('licence', 'type_qualification', 'date_obtention', 'privileges_actifs')
    list_filter = ('type_qualification', 'privileges_actifs')
    search_fields = ('licence__agent__trigram',)
    autocomplete_fields = ('licence',)

@admin.register(MentionUnite)
class MentionUniteAdmin(admin.ModelAdmin):
    # ### CORRECTION ###
    # On remplace 'qualification' par 'qualification_source'
    list_display = ('qualification_source', 'centre', 'type_flux', 'statut', 'date_echeance')
    
    list_filter = ('statut', 'type_flux', 'centre')
    
    # On met à jour les chemins de recherche pour suivre les nouvelles relations
    search_fields = ('qualification_source__licence__agent__trigram', 'mention_particuliere')
    
    # ### CORRECTION ###
    # On remplace 'qualification' par 'qualification_source'
    autocomplete_fields = ('qualification_source', 'centre', 'licence')

@admin.register(MentionLinguistique)
class MentionLinguistiqueAdmin(admin.ModelAdmin):
    list_display = ('licence', 'langue', 'niveau_oaci', 'date_echeance')
    list_filter = ('langue', 'niveau_oaci')
    search_fields = ('licence__agent__trigram',)
    autocomplete_fields = ('licence',)

@admin.register(FormationReglementaire)
class FormationReglementaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'periodicite_ans')
    search_fields = ('nom',)

@admin.register(SuiviFormationReglementaire)
class SuiviFormationReglementaireAdmin(admin.ModelAdmin):
    list_display = ('licence', 'formation', 'date_realisation', 'date_echeance')
    list_filter = ('formation',)
    search_fields = ('licence__agent__trigram',)
    autocomplete_fields = ('licence', 'formation')