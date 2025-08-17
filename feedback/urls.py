# Fichier : feedback/urls.py (Version Corrigée)

from django.urls import path  # <-- CETTE LIGNE MANQUAIT
from . import views

app_name = 'feedback'

urlpatterns = [
    path('soumettre/', views.soumettre_feedback_view, name='soumettre'),
    path('tableau-de-bord/', views.liste_feedback_view, name='tableau-de-bord'),
    path('detail/<int:feedback_id>/', views.detail_feedback_view, name='detail'),
]