# Fichier : cyber/urls.py

from django.urls import path
from . import views

app_name = 'cyber'

urlpatterns = [
    # Vue nationale
    path('dashboard/', views.dashboard_national_view, name='dashboard'),

    # Vues locales (par centre)
    path('smsi/<int:centre_id>/', views.smsi_detail_view, name='smsi-detail'),

    # Vues pour les Risques
    path('smsi/<int:centre_id>/risques/creer/', views.creer_risque_view, name='creer-risque'),
    path('risque/<int:risque_id>/', views.detail_risque_view, name='detail-risque'),

    # Vues pour les Incidents
    path('smsi/<int:centre_id>/incidents/creer/', views.creer_incident_view, name='creer-incident'),
    path('incident/<int:incident_id>/', views.detail_incident_view, name='detail-incident'),

    # Pont depuis le module Technique
    path('incident/creer-depuis-panne/<int:panne_id>/', views.creer_incident_depuis_panne_view, name='creer-incident-depuis-panne'),
]
