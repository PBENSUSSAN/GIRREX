# Fichier : suivi/admin.py

from django.contrib import admin
from .models import Action, HistoriqueAction


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle Action.
    Permet de créer, modifier, et visualiser les actions de suivi.
    """
    list_display = (
        'numero_action', 'titre', 'responsable', 'validateur', 
        'echeance', 'statut', 'avancement', 'date_creation', 'objet_source_display'
    )
    list_filter = (
        'statut', 'priorite', 'statut_echeance', 'echeance', 
        'responsable__centre', 'responsable', 'validateur'
    )
    search_fields = (
        'numero_action', 'titre', 'description', 
        'responsable__trigram', 'responsable__reference', 
        'validateur__trigram', 'validateur__reference'
    )
    date_hierarchy = 'date_creation'
    ordering = ('echeance', 'statut', 'priorite')

    # Utilisation des champs d'autocomplétion pour les ForeignKeys vers Agent
    autocomplete_fields = ['responsable', 'validateur']

    # On affiche l'objet source de manière plus lisible
    def objet_source_display(self, obj):
        if obj.objet_source:
            # On construit un lien vers l'objet source dans l'admin, si possible
            # Cela nécessite que l'objet source soit aussi enregistré dans l'admin
            from django.urls import reverse
            from django.utils.html import format_html
            
            app_label = obj.content_type.app_label
            model_name = obj.content_type.model
            
            try:
                # Tente de construire l'URL de l'objet source dans l'admin
                link = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
                return format_html('<a href="{}">{} ({})</a>', link, str(obj.objet_source), model_name.capitalize())
            except:
                # Si l'URL n'existe pas (par exemple, l'objet source n'est pas dans l'admin)
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

    # Rendre tous les champs en lecture seule car c'est un journal
    readonly_fields = ('action', 'type_evenement', 'auteur', 'timestamp', 'details')

    # Empêcher la création, modification, suppression manuelle
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    # Affiche un aperçu des détails JSON
    def details_preview(self, obj):
        import json
        return json.dumps(obj.details, indent=2)
    details_preview.short_description = "Détails"