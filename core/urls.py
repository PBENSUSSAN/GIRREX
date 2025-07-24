# ==============================================================================
# Fichier : core/urls.py (VERSION FINALE AVEC LOGIQUE DE CLÔTURE)
# Ce fichier définit toutes les routes de l'application 'core'.
# ==============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # --- Vues Générales ---
    path('', views.home, name='home'),
    path('agents/', views.liste_agents, name='liste-agents'), 
    
    # --- URLs pour le Tour de Service (Planning) ---
    path('planning/', views.selecteur_centre_view, name='selecteur-centre'),
    path('planning/centre/<int:centre_id>/', views.tour_de_service_view, name='tour-de-service-centre'),
    path('planning/centre/<int:centre_id>/<int:year>/<int:month>/', views.tour_de_service_view, name='tour-de-service-monthly'),
    
    # --- API pour le Tour de Service ---
    path('api/planning/<int:centre_id>/<int:year>/<int:month>/', views.api_get_planning_data, name='api-get-planning-data'),
    path('ajax/update-tour/', views.update_tour_de_service, name='ajax-update-tour'),
    path('ajax/update-comment/', views.update_tour_de_service_comment, name='ajax-update-comment'),
    
    # --- API pour la gestion des Positions ---
    path('api/centre/<int:centre_id>/positions/', views.api_get_positions, name='api-get-positions'),
    path('api/centre/<int:centre_id>/positions/add/', views.api_add_position, name='api-add-position'),
    path('api/position/<int:position_id>/update/', views.api_update_position, name='api-update-position'),
    path('api/position/<int:position_id>/delete/', views.api_delete_position, name='api-delete-position'),
    
    # --- Gestion des Versions du Planning ---
    path('planning/centre/<int:centre_id>/<int:year>/<int:month>/valider/', views.valider_tour_de_service, name='valider-tour-de-service'), 
    path('planning/centre/<int:centre_id>/versions/', views.liste_versions_validees, name='liste-versions-validees'),
    path('planning/version/<int:version_id>/', views.voir_version_validee, name='voir-version-validee'),

    # ==========================================================================
    # URLs POUR LA FEUILLE DE TEMPS (Corrigées et complétées)
    # ==========================================================================
    
    # URL pour afficher la feuille de temps du jour (aujourd'hui)
    path('feuille-temps/centre/<int:centre_id>/', views.feuille_de_temps_view, name='feuille-temps-jour'),
    
    # URL pour afficher la feuille de temps d'un jour spécifique (navigation)
    path('feuille-temps/centre/<int:centre_id>/<str:jour>/', views.feuille_de_temps_view, name='feuille-temps-specific-jour'),
    
    # --- API pour la Feuille de Temps ---
    path('api/feuille-temps/<int:centre_id>/<str:jour>/', views.api_get_feuille_temps_data, name='api-get-feuille-temps'),
    path('api/feuille-temps/update/', views.api_update_feuille_temps, name='api-update-feuille-temps'),
    path('api/feuille-temps/valider-horaires/', views.api_valider_horaires, name='api-valider-horaires'),
    path('api/feuille-temps/verrou/forcer/', views.api_forcer_verrou, name='api-forcer-verrou'),
    path('api/feuille-temps/cloturer/', views.api_cloturer_journee, name='api-cloturer-journee'),
    path('api/feuille-temps/reouvrir/', views.api_reouvrir_journee, name='api-reouvrir-journee'),
]