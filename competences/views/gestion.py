# Fichier : competences/views/gestion.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.decorators import effective_permission_required
from core.models import Agent
from ..models import Brevet, Qualification
from ..forms import BrevetForm, QualificationForm


@login_required
def gerer_brevet_view(request, agent_id):
    """ Gère la création ou la modification du brevet d'un agent. """
    agent = get_object_or_404(Agent, pk=agent_id)
    brevet = Brevet.objects.filter(agent=agent).first()
    
    if request.method == 'POST':
        form = BrevetForm(request.POST, instance=brevet)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.agent = agent
            instance.save()
            messages.success(request, f"Le brevet de {agent.trigram} a été mis à jour.")
            return redirect('competences:dossier_agent', agent_id=agent.id_agent)
    else:
        form = BrevetForm(instance=brevet)

    context = {
        'form': form,
        'agent_concerne': agent,
        'titre': f"Gérer le Brevet de {agent.trigram}"
    }
    return render(request, 'competences/form_gestion.html', context)


@login_required
def ajouter_qualification_view(request, brevet_id):
    """ Permet d'ajouter une qualification (un jalon de carrière) à un brevet. """
    brevet = get_object_or_404(Brevet, pk=brevet_id)
    
    if request.method == 'POST':
        form = QualificationForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.brevet = brevet
            instance.save()
            messages.success(request, f"La qualification a été ajoutée pour {brevet.agent.trigram}.")
            return redirect('competences:dossier_agent', agent_id=brevet.agent.id_agent)
    else:
        form = QualificationForm()

    context = {
        'form': form,
        'agent_concerne': brevet.agent,
        'titre': f"Ajouter une Qualification pour {brevet.agent.trigram}"
    }
    return render(request, 'competences/form_gestion.html', context)