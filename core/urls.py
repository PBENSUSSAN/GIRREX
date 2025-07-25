# ==============================================================================
# Fichier : core/urls.py (VERSION REFACTORISÉE FINALE)
# ==============================================================================

from django.urls import path
# On importe maintenant nos modules de vues spécifiques
from .views import general, planning, feuille_temps

urlpatterns = [
    # --- Vues Générales ---
    path('', general.home, name='home'),
    path('agents/', general.liste_agents, name='liste-agents'), 
    path('planning/', general.selecteur_centre_view, name='selecteur-centre'),

    # --- Tour de Service (Planning) ---
    path('planning/centre/<int:centre_id>/', planning.tour_de_service_view, name='tour-de-service-centre'),
    path('planning/centre/<int:centre_id>/<int:year>/<int:month>/', planning.tour_de_service_view, name='tour-de-service-monthly'),
    path('planning/centre/<int:centre_id>/versions/', planning.liste_versions_validees, name='liste-versions-validees'),
    path('planning/version/<int:version_id>/', planning.voir_version_validee, name='voir-version-validee'),

    # --- API Tour de Service ---
    path('api/planning/<int:centre_id>/<int:year>/<int:month>/', planning.api_get_planning_data, name='api-get-planning-data'),
    path('ajax/update-tour/', planning.update_tour_de_service, name='ajax-update-tour'),
    path('ajax/update-comment/', planning.update_tour_de_service_comment, name='ajax-update-comment'),
    path('api/centre/<int:centre_id>/positions/', planning.api_get_positions, name='api-get-positions'),
    path('api/centre/<int:centre_id>/positions/add/', planning.api_add_position, name='api-add-position'),
    path('api/position/<int:position_id>/update/', planning.api_update_position, name='api-update-position'),
    path('api/position/<int:position_id>/delete/', planning.api_delete_position, name='api-delete-position'),
    path('planning/centre/<int:centre_id>/<int:year>/<int:month>/valider/', planning.valider_tour_de_service, name='valider-tour-de-service'), 
    
    # --- Feuille de Temps ---
    path('feuille-temps/centre/<int:centre_id>/', feuille_temps.feuille_de_temps_view, name='feuille-temps-jour'),
    path('feuille-temps/centre/<int:centre_id>/<str:jour>/', feuille_temps.feuille_de_temps_view, name='feuille-temps-specific-jour'),
    
    # --- API Feuille de Temps ---
    path('api/feuille-temps/<int:centre_id>/<str:jour>/', feuille_temps.api_get_feuille_temps_data, name='api-get-feuille-temps'),
    path('api/feuille-temps/update/', feuille_temps.api_update_feuille_temps, name='api-update-feuille-temps'),
    path('api/feuille-temps/valider-horaires/', feuille_temps.api_valider_horaires, name='api-valider-horaires'),
    path('api/feuille-temps/verrou/forcer/', feuille_temps.api_forcer_verrou, name='api-forcer-verrou'),
    path('api/feuille-temps/cloturer/', feuille_temps.api_cloturer_journee, name='api-cloturer-journee'),
    path('api/feuille-temps/reouvrir/', feuille_temps.api_reouvrir_journee, name='api-reouvrir-journee'),
]