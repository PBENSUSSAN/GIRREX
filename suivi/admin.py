# Fichier : suivi/admin.py (Corrigé pour le champ 'centres')

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
        'numero_action', 'titre', 'categorie', 
        'responsable', 'echeance', 'statut', 'avancement', 'parent'
        # 'centres' est un champ ManyToMany, on ne peut pas l'afficher directement ici
        # On pourrait créer une méthode personnalisée si nécessaire
    )
    list_filter = (
        'statut', 'categorie', 'priorite', 'centres', 'responsable' # MODIFIÉ
    )
    search_fields = (
        'numero_action', 'titre', 'description', 
        'responsable__trigram', 'responsable__reference',
        'centres__nom_centre', 'centres__code_centre' # MODIFIÉ
    )
    date_hierarchy = 'echeance'
    ordering = ('echeance', 'statut', 'priorite')

    autocomplete_fields = ['responsable', 'parent', 'centres'] # MODIFIÉ
    
    fieldsets = (
        ('Identification', {
            'fields': ('numero_action', 'titre', 'description')
        }),
        ('Classification & Périmètre', {
            'fields': ('categorie', 'centres', 'objet_source_display') # MODIFIÉ
        }),
        ('Pilotage', {
            'fields': ('responsable', 'echeance', 'priorite', 'statut', 'avancement')
        }),
        ('Hiérarchie', {
            'fields': ('parent',)
        }),
    )

    readonly_fields = ('numero_action', 'objet_source_display')

    actions = ['archiver_les_actions']

    def archiver_les_actions(self, request, queryset):
        actions_a_archiver = queryset.filter(statut=Action.StatutAction.VALIDEE)
        rows_updated = actions_a_archiver.update(statut=Action.StatutAction.ARCHIVEE)
        self.message_user(request, f"{rows_updated} action(s) ont été archivées avec succès.")
    
    archiver_les_actions.short_description = "Archiver les actions sélectionnées (si Validées)"
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
    """
    list_display = ('timestamp', 'action', 'type_evenement', 'auteur', 'details_preview')
    list_filter = ('type_evenement', 'timestamp', 'action__statut')
    search_fields = ('action__titre', 'details', 'auteur__username')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    actions = ['delete_selected']

    def details_preview(self, obj):
        import json
        try:
            return json.dumps(obj.details, indent=2, ensure_ascii=False)
        except TypeError:
            return obj.details
    details_preview.short_description = "Détails"

@admin.register(PriseEnCompte)
class PriseEnCompteAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle PriseEnCompte.
    """
    list_display = ('id', 'action_agent', 'agent', 'timestamp')
    list_filter = ('timestamp', 'agent__centre')
    search_fields = ('agent__trigram', 'action_agent__titre')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    autocomplete_fields = ['action_agent', 'agent']
    readonly_fields = ('action_agent', 'agent', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False