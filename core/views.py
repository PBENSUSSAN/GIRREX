from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Agent # Assurez-vous que Agent est importé si vous l'utilisez

# NOUVELLE VUE POUR LA PAGE D'ACCUEIL
@login_required
def home(request):
    """
    Vue pour la page d'accueil (tableau de bord).
    Nécessite que l'utilisateur soit connecté pour y accéder.
    """
    # Pour l'instant, on ne passe aucune donnée complexe.
    # On pourrait plus tard ajouter des statistiques, des alertes, etc.
    context = {} 
    return render(request, 'core/home.html', context)


@login_required
def liste_agents(request):
    """
    Vue pour afficher la liste de tous les agents.
    """
    agents = Agent.objects.all().order_by('reference')
    context = {
        'agents': agents,
    }
    return render(request, 'core/liste_agents.html', context)