# Fichier : qs/urls.py

from django.urls import path
from . import views

app_name = 'qs'

urlpatterns = [
    path('tableau-bord-national/', views.tableau_bord_qs_national_view, name='tableau-bord-qs-national'),
    path('tableau-bord/', views.tableau_bord_qs_view, name='tableau-bord-qs'),
    # URL pour notre formulaire de pré-déclaration.
    # Elle prend l'ID du centre en paramètre.
    path('pre-declarer/<int:centre_id>/', views.pre_declarer_fne_view, name='pre-declarer-fne'),

     # URL pour la vue de détail d'une FNE
    path('fne/<int:fne_id>/detail/', views.detail_fne_view, name='detail-fne'),
    # URL pour lie plusieurs FNE
    path('fne/<int:fne_id_principal>/regrouper/', views.regrouper_fne_view, name='regrouper-fne'),
    # URL pour lrapport externe
    path('dossier/<int:dossier_id>/ajouter-rapport/', views.ajouter_rapport_externe_view, name='ajouter-rapport-externe'),
    path('dossier/<int:dossier_id>/detail/', views.detail_dossier_view, name='detail-dossier'),
    # URL pour esoldariser
    path('fne/<int:fne_id>/desolidariser/', views.desolidariser_fne_view, name='desolidariser-fne'),
]