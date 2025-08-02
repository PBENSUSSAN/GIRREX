# Fichier : suivi/urls.py

from django.urls import path
from . import views

app_name = 'suivi'

urlpatterns = [
    # URLs de base
    path('actions/', views.tableau_actions_view, name='tableau-actions'),
    path('actions/creer/', views.create_action_view, name='create-action'),
    path('action/<int:action_id>/', views.detail_action_view, name='detail-action'),
    
    # URLs de Workflow
    
    # Aiguillage vers la page de dispatch pour une diffusion documentaire (vers tous les agents)
    path('action/<int:action_id>/diffuser_agents/', views.lancer_diffusion_agents_view, name='diffuser-agents'),
    
    # Aiguillage vers la page de dispatch pour une diffusion QS (vers les animateurs QS)
    path('action/<int:action_id>/diffuser_qs/', views.diffuser_aux_animateurs_qs_view, name='diffuser-qs'),

    # La page de dispatch générique (utilisée par les deux vues ci-dessus)
    # Note : Cette URL n'est pas appelée directement, mais via les vues d'aiguillage.
    # On pourrait la nommer si on voulait y accéder directement un jour.
    
    # Action de validation pour l'agent final
    path('action/<int:action_id>/valider_prise_en_compte/', views.valider_prise_en_compte_view, name='valider-prise-en-compte'),
    
    # Action de validation pour un responsable (étape à 99%)
    path('action/<int:action_id>/valider_etape/', views.valider_etape_responsable_view, name='valider-etape'),
    
    # Action de clôture finale réservée au Responsable SMS
    path('action/<int:action_id>/cloture_sms/', views.cloture_finale_sms_view, name='cloture-sms'),

    # Action d'archivage
    path('actions/archiver/', views.archiver_actions_view, name='archiver-actions'),
    path('archives/', views.archives_actions_view, name='archives-actions'),
]