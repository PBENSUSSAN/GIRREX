# ==============================================================================
# Fichier : core/urls.py (VERSION FINALE COMPLÈTE)
# ==============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # URLs existantes
    path('', views.home, name='home'),
    path('agents/', views.liste_agents, name='liste-agents'), 
    
    # --- URLs POUR LE TOUR DE SERVICE ---
    path('planning/', views.selecteur_centre_view, name='selecteur-centre'),
    path('planning/centre/<int:centre_id>/', views.tour_de_service_view, name='tour-de-service-centre'),
    path('planning/centre/<int:centre_id>/<int:year>/<int:month>/', views.tour_de_service_view, name='tour-de-service-monthly'),
    
    # --- URLs AJAX POUR LE PLANNING ---
    path('ajax/update-tour/', views.update_tour_de_service, name='ajax-update-tour'),
    path('ajax/update-comment/', views.update_tour_de_service_comment, name='ajax-update-comment'),
    
    # --- URLs API POUR LA CONFIGURATION DES POSITIONS ---
    path('api/centre/<int:centre_id>/positions/', views.api_get_positions, name='api-get-positions'),
    path('api/centre/<int:centre_id>/positions/add/', views.api_add_position, name='api-add-position'),
    path('api/position/<int:position_id>/update/', views.api_update_position, name='api-update-position'),
    path('api/position/<int:position_id>/delete/', views.api_delete_position, name='api-delete-position'),
]