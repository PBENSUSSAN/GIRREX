from django.contrib import admin
from .models import PanneCentre

@admin.register(PanneCentre)
class PanneCentreAdmin(admin.ModelAdmin):
    list_display = ('date_heure_debut', 'equipement_concerne', 'criticite', 'statut', 'centre', 'auteur', 'notification_generale')
    list_filter = ('centre', 'criticite', 'statut', 'date_heure_debut')
    search_fields = ('equipement_concerne', 'description', 'auteur__trigram')
    autocomplete_fields = ['centre', 'auteur']
    date_hierarchy = 'date_heure_debut'