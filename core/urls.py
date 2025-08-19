# Fichier : core/urls.py (Corrigé pour la sélection par Rôle)

from django.urls import path
from .views import general, planning, feuille_temps, cahier_de_marche, zone, medical

urlpatterns = [
    # --- Vues Générales ---
    path('', general.home, name='home'),
    path('agents/', general.liste_agents, name='liste-agents'), 
    path('planning/', general.selecteur_centre_view, name='selecteur-centre'),

    # ==============================================================================
    # URLS POUR LE CHANGEMENT DE CONTEXTE (MODIFIÉES)
    # On utilise maintenant l'ID de l'objet AgentRole pour une sélection plus fine.
    # ==============================================================================
    path('contexte/definir-role/<int:agent_role_id>/', general.definir_contexte_role, name='definir_contexte_role'),
   


    # ==============================================================================
    # NOUVEAUX "HUBS" DE REDIRECTION (INCHANGÉS)
    # ==============================================================================
    path('tour-de-service/hub/', general.tour_de_service_hub_view, name='tour-de-service-hub'),
    path('cahier-de-marche/hub/', general.cahier_de_marche_hub_view, name='cahier-de-marche-hub'),


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
    
    # --- Feuille de Temps & Service ---
    path('feuille-temps/centre/<int:centre_id>/', feuille_temps.feuille_de_temps_view, name='feuille-temps-jour'),
    path('feuille-temps/centre/<int:centre_id>/<str:jour>/', feuille_temps.feuille_de_temps_view, name='feuille-temps-specific-jour'),
    path('service/centre/<int:centre_id>/<str:action>/', feuille_temps.gerer_service_view, name='gerer-service'),
    
    # --- API Feuille de Temps ---
    path('api/feuille-temps/<int:centre_id>/<str:jour>/', feuille_temps.api_get_feuille_temps_data, name='api-get-feuille-temps'),
    path('api/feuille-temps/update/', feuille_temps.api_update_feuille_temps, name='api-update-feuille-temps'),
    path('api/feuille-temps/valider-horaires/', feuille_temps.api_valider_horaires, name='api-valider-horaires'),
    path('api/feuille-temps/verrou/forcer/', feuille_temps.api_forcer_verrou, name='api-forcer-verrou'),
    
    # --- Cahier de Marche ---
    path('cahier-de-marche/centre/<int:centre_id>/<str:jour>/', cahier_de_marche.cahier_de_marche_view, name='cahier-de-marche'),
    path('cahier-de-marche/centre/<int:centre_id>/panne/ajouter/', cahier_de_marche.ajouter_panne_view, name='ajouter-panne'),
    path('cahier-de-marche/centre/<int:centre_id>/evenement/ajouter/', cahier_de_marche.ajouter_evenement_view, name='ajouter-evenement'),
    path('cahier-de-marche/centre/<int:centre_id>/panne/<int:panne_id>/resoudre/', cahier_de_marche.resoudre_panne_view, name='resoudre-panne'),

     # --- gestion zone ---
    path('gestion-zone/centre/<int:centre_id>/', zone.gestion_zone_view, name='gestion-zone'),
    path('gestion-zone/zone/<int:centre_id>/<int:zone_id>/<str:action>/', zone.activer_desactiver_zone_view, name='activer-desactiver-zone'),
    
    # --- API Gestion des Zones ---
    path('api/zones/list/<int:centre_id>/', zone.api_get_zones, name='api-zone-list'),
    path('api/zones/add/<int:centre_id>/', zone.api_add_zone, name='api-zone-add'),
    path('api/zones/update/<int:zone_id>/', zone.api_update_zone, name='api-zone-update'),
    path('api/zones/delete/<int:zone_id>/', zone.api_delete_zone, name='api-zone-delete'),

    # ### DÉBUT DES NOUVELLES URLS MÉDICALES ###
    path(
        'agent/<int:agent_id>/rdv-medical/planifier/', 
        medical.gerer_rdv_medical_view, 
        name='planifier_rdv_medical'
    ),
    path(
        'rdv-medical/<int:rdv_id>/modifier/', 
        medical.gerer_rdv_medical_view, 
        name='modifier_rdv_medical'),
    path('rdv-medical/<int:rdv_id>/saisir-resultat/', medical.enregistrer_resultat_visite_view, name='saisir_resultat_visite'),
]