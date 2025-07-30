# Fichier : suivi/urls.py

from django.urls import path
from . import views

app_name = 'suivi' # Important pour les URLs nommées

urlpatterns = [
    path('actions/', views.tableau_actions_view, name='tableau-actions'),
    # Nous ajouterons d'autres URLs ici plus tard (ex: pour voir le détail d'une action)
]