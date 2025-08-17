# Fichier : feedback/admin.py

from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'categorie', 'module_concerne', 'created_at')
    list_filter = ('categorie', 'module_concerne', 'created_at')
    search_fields = ('titre', 'description', 'auteur__trigram')
    readonly_fields = ('auteur', 'created_at')