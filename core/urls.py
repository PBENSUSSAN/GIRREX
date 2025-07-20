# ==============================================================================
# Fichier : core/urls.py (VERSION FINALE ET COHÉRENTE)
# ==============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # URLs existantes
    path('', views.home, name='home'),
    path('agents/', views.liste_agents, name='liste-agents'), 
    
    # --- URLs POUR LE TOUR DE SERVICE ---
    path('planning/', views.selecteur_centre_view, name='selecteur-centre'),

    # URL pour afficher le planning d'un centre
    path('planning/centre/<int:centre_id>/', views.tour_de_service_view, name='tour-de-service-centre'),
    
    # CORRECTION : Le nom est bien défini ici
    path('planning/centre/<int:centre_id>/<int:year>/<int:month>/', views.tour_de_service_view, name='tour-de-service-monthly'),
    
    # URLs AJAX
    path('ajax/update-tour/', views.update_tour_de_service, name='ajax-update-tour'),
    path('ajax/update-comment/', views.update_tour_de_service_comment, name='ajax-update-comment'),
]