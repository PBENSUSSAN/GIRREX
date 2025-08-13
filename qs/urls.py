# Fichier : qs/urls.py

from django.urls import path
from . import views

app_name = 'qs'

urlpatterns = [
    # URLs conservées et adaptées
    path('tableau-bord/', views.tableau_bord_qs_view, name='tableau-bord-qs'),
    path('pre-declarer/<int:centre_id>/', views.pre_declarer_fne_view, name='pre-declarer-fne'),
    path('fne/<int:fne_id>/detail/', views.detail_fne_view, name='detail-fne'),

    # URL modifiée : elle est maintenant liée à une FNE, pas à un dossier
    path('fne/<int:fne_id>/ajouter-rapport/', views.ajouter_rapport_externe_view, name='ajouter-rapport-externe'),
    #URL pour reco qs
    path('fne/<int:fne_id>/ajouter-recommandation/', views.ajouter_recommandation_view, name='ajouter-recommandation'),
    
]