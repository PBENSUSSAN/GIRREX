# ==============================================================================
# Fichier : core/views/general.py
# Vues générales de l'application (accueil, listes, sélecteurs).
# ==============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# On utilise un import relatif pour accéder aux modèles et décorateurs de l'application
from ..models import Agent, Centre
from ..decorators import effective_permission_required

@login_required
def home(request):
    """ Affiche la page d'accueil / le tableau de bord. """
    context = {} 
    return render(request, 'core/home.html', context)

@effective_permission_required('core.view_agent')
def liste_agents(request):
    """ Affiche la liste de tous les agents. """
    agents = Agent.objects.all().order_by('reference')
    context = {'agents': agents}
    return render(request, 'core/liste_agents.html', context)

@login_required
def selecteur_centre_view(request):
    """ 
    Permet à un utilisateur de choisir un centre.
    Redirige automatiquement vers le TDS si l'utilisateur est rattaché à un centre.
    """
    try:
        user_centre = request.user.agent_profile.centre
        if user_centre:
            return redirect('tour-de-service-centre', centre_id=user_centre.id)
    except (AttributeError, Agent.DoesNotExist):
        # Si l'utilisateur (ex: superuser) n'a pas de profil agent, on le laisse choisir un centre.
        pass
    centres = Centre.objects.all()
    context = {'centres': centres}
    return render(request, 'core/selecteur_centre.html', context)