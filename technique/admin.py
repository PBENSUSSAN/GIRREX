# Fichier : technique/admin.py

from django.contrib import admin
from .models import PanneCentre, Miso, MisoHistorique, PanneHistorique

# Enregistrement du modèle PanneCentre avec la configuration d'affichage
@admin.register(PanneCentre)
class PanneCentreAdmin(admin.ModelAdmin):
    # On utilise les NOUVEAUX champs : 'type_equipement' et 'equipement_details'
    # L'ancien champ 'equipement_concerne' a été retiré.
    list_display = (
        'date_heure_debut', 
        'type_equipement', 
        'equipement_details', 
        'criticite', 
        'statut', 
        'centre', 
        'auteur'
    )
    
    # On filtre sur le nouveau champ 'type_equipement'
    list_filter = (
        'centre', 
        'criticite', 
        'statut', 
        'type_equipement', 
        'date_heure_debut'
    )
    
    # On recherche dans les nouveaux champs
    search_fields = (
        'type_equipement', 
        'equipement_details', 
        'description', 
        'auteur__trigram'
    )
    
    autocomplete_fields = ['centre', 'auteur']
    date_hierarchy = 'date_heure_debut'

# Enregistrement des autres modèles du module 'technique' pour qu'ils apparaissent dans l'admin.
# C'est une bonne pratique de les enregistrer pour pouvoir les consulter.
admin.site.register(Miso)
admin.site.register(MisoHistorique)
admin.site.register(PanneHistorique)