# Fichier : suivi/urls.py (Version Finale avec la Nouvelle Vue de Diffusion)

from django.urls import path
from . import views

app_name = 'suivi'

urlpatterns = [
    # URLs de base
    path('actions/', views.tableau_actions_view, name='tableau-actions'),
    path('actions/creer/', views.create_action_view, name='create-action'),
    path('action/<int:action_id>/', views.detail_action_view, name='detail-action'),
    
    # Nouveau workflow de diffusion
    path('diffuser/<int:content_type_id>/<int:object_id>/', views.lancer_diffusion_view, name='lancer-diffusion'),

    # Workflow de validation et clôture
    path('action/<int:action_id>/valider_prise_en_compte/', views.valider_prise_en_compte_view, name='valider-prise-en-compte'),
    path('action/<int:action_id>/valider_etape/', views.valider_etape_responsable_view, name='valider-etape'),
    path('action/<int:action_id>/cloture_initiateur/', views.cloture_initiateur_view, name='cloture-initiateur'),
    path('action/<int:action_id>/cloture_sms/', views.cloture_finale_sms_view, name='cloture-sms'),

    # Gestion des archives
    path('actions/archiver/', views.archiver_actions_view, name='archiver-actions'),
    path('archives/', views.archives_actions_view, name='archives-actions'),
]