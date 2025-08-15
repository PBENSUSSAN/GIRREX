# Fichier : es/urls.py

from django.urls import path
from . import views

app_name = 'es'

urlpatterns = [
    path('tableau-bord/', views.tableau_etudes_view, name='tableau-etudes'),
    path('lancer-changement/', views.lancer_changement_view, name='lancer-changement'),
    path('changement/<int:changement_id>/detail/', views.detail_changement_view, name='detail-changement'),
    path('changement/<int:changement_id>/classifier/', views.classifier_changement_view, name='classifier-changement'),
    path('etude/<int:etude_id>/detail/', views.detail_etude_view, name='detail-etude'),
    path('changements-a-classifier/', views.liste_changements_view, name='liste-changements'),
    path('etape/<int:etape_id>/uploader-preuve/', views.uploader_preuve_view, name='uploader-preuve'),
    path('etape/<int:etape_id>/valider/', views.valider_etape_view, name='valider-etape'),
     path('etude/<int:etude_id>/creer-action-formation/', views.creer_action_formation_view, name='creer-action-formation'),
]