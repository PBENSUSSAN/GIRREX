# Fichier : competences/urls.py

from django.urls import path
# ### CORRECTION ### : On importe les modules spécifiques 'dossier' et 'gestion'
from .views import dossier, gestion

app_name = 'competences'

urlpatterns = [
    # Vues de consultation depuis le module 'dossier'
    path('tableau-de-bord/', dossier.tableau_bord_competences_view, name='tableau_bord'),
    path('journal-audit/', dossier.journal_audit_competences_view, name='journal_audit'),

    path('agent/<int:agent_id>/', dossier.dossier_competence_view, name='dossier_competence'),

    # Vues de gestion depuis le module 'gestion'
    path('agent/<int:agent_id>/gerer-licence/', gestion.gerer_licence_view, name='gerer_licence'),
    path('licence/<int:licence_id>/ajouter-qualification/', gestion.ajouter_qualification_view, name='ajouter_qualification'),
     path('qualification/<int:qualification_id>/modifier/', gestion.modifier_qualification_view, name='modifier_qualification'),
    
    # URL pour la création d'une mention
    path('licence/<int:licence_id>/ajouter-mention/', gestion.gerer_mention_unite_view, name='ajouter_mention'),
    # URL pour la modification d'une mention
    path('mention/<int:mention_id>/modifier/', gestion.gerer_mention_unite_view, name='modifier_mention'),

    
]
