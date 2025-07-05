# Fichier : core/urls.py (celui que vous venez de créer)

from django.urls import path
from . import views  # Importe les vues depuis le fichier views.py du même dossier

# 'urlpatterns' est le nom de variable standard que Django recherche.
urlpatterns = [
    # On définit l'URL qui causait l'erreur
    path('', views.home, name='home'),
    path('agents/', views.liste_agents, name='liste-agents'),
]