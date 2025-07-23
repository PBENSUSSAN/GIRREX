# ==============================================================================
# Fichier : core/urls.py (VERSION COMPLÈTE ET REFACTORISÉE)
# Ce fichier définit toutes les routes de l'application 'core'.
# ==============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # --- Vues Générales ---
    path('', views.home, name='home'),
    path('agents/', views.liste_agents, name='liste-agents'), 
    
    # --- URLs pour l'affichage des pages du Tour de Service (Squelette HTML) ---
    path('planning/', views.selecteur_centre_view, name='selecteur-centre'),
    path('planning/centre/<int:centre_id>/', views.tour_de_service_view, name='tour-de-service-centre'),
    path('planning/centre/<int:centre_id>/<int:year>/<int:month>/', views.tour_de_service_view, name='tour-de-service-monthly'),
    
    # --- API & AJAX ---
    
    # NOUVELLE ROUTE API pour charger les données complètes du planning de manière asynchrone
    path('api/planning/<int:centre_id>/<int:year>/<int:month>/', views.api_get_planning_data, name='api-get-planning-data'),
    
    # Routes AJAX pour la mise à jour des cellules et des commentaires (inchangées)
    path('ajax/update-tour/', views.update_tour_de_service, name='ajax-update-tour'),
    path('ajax/update-comment/', views.update_tour_de_service_comment, name='ajax-update-comment'),
    
    # API pour la gestion des Positions (inchangées)
    path('api/centre/<int:centre_id>/positions/', views.api_get_positions, name='api-get-positions'),
    path('api/centre/<int:centre_id>/positions/add/', views.api_add_position, name='api-add-position'),
    path('api/position/<int:position_id>/update/', views.api_update_position, name='api-update-position'),
    path('api/position/<int:position_id>/delete/', views.api_delete_position, name='api-delete-position'),
    
    # --- Gestion des Versions du Planning ---
    path('planning/centre/<int:centre_id>/<int:year>/<int:month>/valider/', views.valider_tour_de_service, name='valider-tour-de-service'), 
    path('planning/centre/<int:centre_id>/versions/', views.liste_versions_validees, name='liste-versions-validees'),
    path('planning/version/<int:version_id>/', views.voir_version_validee, name='voir-version-validee'),
]