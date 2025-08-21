# Fichier : activites/urls.py

from django.urls import path
from . import views

app_name = 'activites'

urlpatterns = [
    # Page principale qui liste les missions de la journée
    path('saisie/<int:centre_id>/<str:date_str>/', views.liste_missions_jour_view, name='saisie_jour'),
    
    # URL pour traiter le formulaire de création de mission (vol parent)
    path('saisie/<int:centre_id>/ajouter-mission/', views.ajouter_mission_view, name='ajouter_mission'),

    # Page de détail d'une mission (affiche tous les segments/relèves)
    path('mission/<int:mission_id>/', views.detail_mission_view, name='detail_mission'),

    # URL pour traiter l'ajout d'une relève à une mission
    path('mission/<int:mission_id>/ajouter-releve/', views.ajouter_releve_view, name='ajouter_releve'),
    
    # URL pour traiter l'ajout d'un participant à un segment de vol
    path('segment/<int:segment_id>/ajouter-participant/', views.ajouter_participant_view, name='ajouter_participant'),

    path('segment/<int:segment_id>/saisir-reel/', views.saisir_heures_reelles_view, name='saisir_heures_reelles'),
    
    # URL pour supprimer un participant
    path('participant/<int:activite_id>/supprimer/', views.supprimer_participant_view, name='supprimer_participant'),
]