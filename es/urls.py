# Fichier : es/urls.py

from django.urls import path
from . import views

app_name = 'es'

urlpatterns = [
    path('tableau-bord/', views.tableau_etudes_view, name='tableau-etudes'),
    path('lancer-changement/', views.lancer_changement_view, name='lancer-changement'),
    path('changement/<int:changement_id>/classifier/', views.classifier_changement_view, name='classifier-changement'),
    path('etude/<int:etude_id>/detail/', views.detail_etude_view, name='detail-etude'),
    path('changements-a-classifier/', views.liste_changements_view, name='liste-changements'),
]