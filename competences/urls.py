# Fichier : competences/urls.py

from django.urls import path
from .views import dossier, gestion, mua


app_name = 'competences'

urlpatterns = [
    # Vues de consultation
    path('tableau-de-bord/', dossier.tableau_bord_view, name='tableau_bord'),
    path('journal-audit/', dossier.journal_audit_view, name='journal_audit'),
    path('agent/<int:agent_id>/', dossier.dossier_agent_view, name='dossier_agent'),

    path('mua/<int:mua_id>/', mua.dossier_mua_view, name='dossier_mua'),
    path('mua/<int:mua_id>/releve-mensuel/', mua.releve_mensuel_view, name='releve_mensuel_mua'),

    # Vues de gestion
    path('agent/<int:agent_id>/gerer-brevet/', gestion.gerer_brevet_view, name='gerer_brevet'),
    path('brevet/<int:brevet_id>/ajouter-qualification/', gestion.ajouter_qualification_view, name='ajouter_qualification'),
]