# Fichier : suivi/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Action, HistoriqueAction, PriseEnCompte

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle Action.
    """
    list_display = (
        'numero_action', 'titre', 'categorie', 'centre', 
        'responsable', 'echeance', 'statut', 'avancement', 'parent'
    )
    list_filter = (
        'statut', 'categorie', 'priorite', 'centre', 'responsable'
    )
    search_fields = (
        'numero_action', 'titre', 'description', 
        'responsable__trigram', 'responsable__reference'
    )
    date_hierarchy = 'echeance' # On utilise l'échéance comme hiérarchie principale
    ordering = ('echeance', 'statut', 'priorite')

    autocomplete_fields = ['responsable', 'parent', 'centre']
    
    # On ajoute des fieldsets pour une meilleure organisation
    fieldsets = (
        ('Identification', {
            'fields': ('numero_action', 'titre', 'description')
        }),
        ('Classification & Périmètre', {
            'fields': ('categorie', 'centre', 'objet_source')
        }),
        ('Pilotage', {
            'fields': ('responsable', 'echeance', 'priorite', 'statut', 'avancement')
        }),
        ('Hiérarchie', {
            'fields': ('parent',)
        }),
    )

    # On rend certains champs en lecture seule pour éviter les erreurs manuelles
    readonly_fields = ('numero_action', 'objet_source_display')

    def objet_source_display(self, obj):
        if obj.objet_source:
            app_label = obj.content_type.app_label
            model_name = obj.content_type.model
            try:
                link = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
                return format_html('<a href="{}">{} ({})</a>', link, str(obj.objet_source), model_name.capitalize())
            except:
                return f"{str(obj.objet_source)} ({model_name.capitalize()})"
        return "N/A"
    objet_source_display.short_description = "Objet Source"


@admin.register(HistoriqueAction)
class HistoriqueActionAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle HistoriqueAction.
    C'est un journal, donc il est en lecture seule.
    """
    list_display = ('timestamp', 'action', 'type_evenement', 'auteur', 'details_preview')
    list_filter = ('type_evenement', 'timestamp', 'action__statut')
    search_fields = ('action__titre', 'details', 'auteur__username')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    actions = ['delete_selected']

    # Rendre tous les champs en lecture seule car c'est un journal
    #readonly_fields = ('action', 'type_evenement', 'auteur', 'timestamp', 'details')

    # Empêcher la création, modification, suppression manuelle
    #def has_add_permission(self, request):
     #   return False

    #def has_change_permission(self, request, obj=None):
     #   return False

    #def has_delete_permission(self, request, obj=None):
     #   return False
    
    # Affiche un aperçu des détails JSON
    def details_preview(self, obj):
        import json
        return json.dumps(obj.details, indent=2)
    details_preview.short_description = "Détails"

@admin.register(PriseEnCompte)
class PriseEnCompteAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle PriseEnCompte.
    Permet de visualiser les preuves de validation des agents.
    """
    list_display = ('id', 'action_agent', 'agent', 'timestamp')
    list_filter = ('timestamp', 'agent__centre')
    search_fields = ('agent__trigram', 'action_agent__titre')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    # On utilise l'autocomplétion pour faciliter la recherche
    autocomplete_fields = ['action_agent', 'agent']

    # Ce modèle est une preuve, il est donc préférable de le mettre en lecture seule
    # pour éviter les modifications manuelles accidentelles.
    readonly_fields = ('action_agent', 'agent', 'timestamp')

    def has_add_permission(self, request):
        # Personne ne doit pouvoir créer une "preuve" manuellement
        return False

    def has_change_permission(self, request, obj=None):
        # On peut autoriser la modification si besoin, mais la lecture seule est plus sûre
        return False # Mettre sur True si vous voulez pouvoir modifier