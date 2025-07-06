# Fichier : core/views.py (VERSION FINALE)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Agent
# On importe notre nouveau décorateur
from .decorators import effective_permission_required

@login_required
def home(request):
    context = {} 
    return render(request, 'core/home.html', context)

# On utilise notre décorateur personnalisé
@effective_permission_required('core.view_agent')
def liste_agents(request):
    agents = Agent.objects.all().order_by('reference')
    context = {
        'agents': agents,
    }
    return render(request, 'core/liste_agents.html', context)