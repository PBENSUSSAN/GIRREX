# Fichier : activites/admin.py

from django.contrib import admin
from .models import Vol, SaisieActivite

class SaisieActiviteInline(admin.TabularInline):
    """
    Permet d'ajouter des activités (participations d'agents)
    directement depuis la page d'un Vol. C'est beaucoup plus pratique.
    """
    model = SaisieActivite
    # Permet de chercher un agent par son nom/trigramme au lieu d'une liste déroulante
    autocomplete_fields = ('agent',)
    # Affiche 2 lignes vides par défaut pour encourager la saisie (contrôleur + CDQ)
    extra = 2

@admin.register(Vol)
class VolAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour le modèle Vol.
    """
    list_display = ('indicatif', 'date_vol', 'flux', 'centre', 'duree')
    list_filter = ('centre', 'flux', 'date_vol')
    search_fields = ('indicatif',)
    date_hierarchy = 'date_vol'
    # Ajoute la gestion des SaisieActivite directement dans la page du Vol
    inlines = [SaisieActiviteInline]

@admin.register(SaisieActivite)
class SaisieActiviteAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour le modèle SaisieActivite.
    Utile pour voir toutes les activités d'un coup, indépendamment des vols.
    """
    list_display = ('vol', 'agent', 'role')
    list_filter = ('role', 'agent__centre', 'agent')
    search_fields = ('vol__indicatif', 'agent__trigram')
    autocomplete_fields = ('vol', 'agent')