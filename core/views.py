# Fichier : core/views.py (VERSION STABLE COMPLÈTE - FIN ÉTAPE 4)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from .models import Agent

@login_required
def home(request):
    """
    Vue pour la page d'accueil (tableau de bord).
    """
    # Dans cette version stable, la vue home n'a pas besoin de logique de permission.
    context = {} 
    return render(request, 'core/home.html', context)

@permission_required('core.view_agent', raise_exception=True)
def liste_agents(request):
    """
    Vue pour afficher la liste de tous les agents.
    Protégée par la permission standard de Django.
    """
    agents = Agent.objects.all().order_by('reference')
    context = {
        'agents': agents,
    }
    return render(request, 'core/liste_agents.html', context)