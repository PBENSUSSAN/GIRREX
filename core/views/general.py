# Fichier : core/views/general.py (Intégral et Corrigé)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from ..models import Agent, Centre, AgentRole

def home(request):
    """ Affiche la page d'accueil. """
    return render(request, 'core/home.html')

@login_required
def liste_agents(request):
    """ Affiche la liste de tous les agents. """
    agents = Agent.objects.select_related('centre', 'user').filter(actif=True)
    return render(request, 'core/liste_agents.html', {'agents': agents})

@login_required
def selecteur_centre_view(request):
    """
    Page générique permettant de choisir un centre pour accéder à une vue locale.
    La vue de destination est passée en paramètre GET 'next_view'.
    """
    next_view_name = request.GET.get('next_view', 'tour-de-service-centre')
    
    if next_view_name == 'cahier-de-marche':
        titre = "Sélectionner un centre pour voir son Cahier de Marche"
    else:
        titre = "Sélectionner un centre pour voir son Tour de Service"

    centres = Centre.objects.all().order_by('code_centre')
    
    context = {
        'centres': centres,
        'next_view_name': next_view_name,
        'titre': titre,
        'today_str': timezone.now().strftime('%Y-%m-%d')
    }
    return render(request, 'core/selecteur_centre.html', context)


# ==============================================================================
# "HUB" DE REDIRECTION POUR LE TOUR DE SERVICE
# ==============================================================================
@login_required
def tour_de_service_hub_view(request):
    """
    Aiguille l'utilisateur vers le bon endroit pour le Tour de Service.
    """
    if not hasattr(request.user, 'agent_profile'):
        return redirect('home')
        
    user_agent = request.user.agent_profile
    
    if user_agent.centre:
        # Un agent local est redirigé directement vers le planning de son centre.
        return redirect('tour-de-service-centre', centre_id=user_agent.centre.id)
    else:
        # Un agent national est redirigé vers le sélecteur.
        base_url = reverse('selecteur-centre')
        query_string = '?next_view=tour-de-service-centre'
        return redirect(base_url + query_string)


# ==============================================================================
# "HUB" DE REDIRECTION POUR LE CAHIER DE MARCHE
# ==============================================================================
@login_required
def cahier_de_marche_hub_view(request):
    """
    Aiguille l'utilisateur vers le bon endroit pour le Cahier de Marche.
    """
    if not hasattr(request.user, 'agent_profile'):
        return redirect('home')
        
    user_agent = request.user.agent_profile
    
    if user_agent.centre:
        today_str = timezone.now().strftime('%Y-%m-%d')
        return redirect('cahier-de-marche', centre_id=user_agent.centre.id, jour=today_str)
    else:
        base_url = reverse('selecteur-centre')
        query_string = '?next_view=cahier-de-marche'
        return redirect(base_url + query_string)

@login_required
def definir_contexte_role(request, agent_role_id):
    """
    Met à jour le rôle actif dans la session de l'utilisateur.
    """
    try:
        # On vérifie que l'AgentRole demandé appartient bien à l'utilisateur connecté.
        agent_role = AgentRole.objects.get(pk=agent_role_id, agent=request.user.agent_profile)
        
        # On stocke l'ID de l'assignation de rôle.
        request.session['selected_agent_role_id'] = agent_role.id
        
    except AgentRole.DoesNotExist:
        # Si l'utilisateur essaie d'usurper un rôle, on ne fait rien ou on logue une erreur.
        messages.error(request, "Vous n'avez pas accès à ce rôle.")
        pass 
    
    return redirect('home')


@login_required
def reinitialiser_contexte_centre(request):
    """
    Supprime le contexte de centre de la session pour revenir à la vue par défaut (nationale).
    """
    if 'selected_centre_id' in request.session:
        # Si une sélection existait, on la supprime.
        del request.session['selected_centre_id']
    
    return redirect('home')
