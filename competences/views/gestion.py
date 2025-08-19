# Fichier : competences/views/gestion.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from core.decorators import effective_permission_required
from core.models import Agent
from ..models import Licence, Qualification, MentionUnite
from ..forms import LicenceForm, QualificationForm, MentionUniteForm


@login_required
@effective_permission_required('competences.change_licence', raise_exception=True)
def gerer_licence_view(request, agent_id):
    """
    Gère la création (si elle n'existe pas) ou la modification
    de la licence principale d'un agent.
    """
    agent = get_object_or_404(Agent, pk=agent_id)
    licence = Licence.objects.filter(agent=agent).first()
    
    if request.method == 'POST':
        form = LicenceForm(request.POST, instance=licence)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.agent = agent
            instance.save()
            messages.success(request, f"Le dossier de licence de {agent.trigram} a été mis à jour.")
            return redirect('competences:dossier_competence', agent_id=agent.id_agent)
    else:
        form = LicenceForm(instance=licence)

    context = {
        'form': form,
        'agent_concerne': agent,
        'titre': f"Gérer la Licence de {agent.trigram}"
    }
    return render(request, 'competences/form_gestion.html', context)


@login_required
@effective_permission_required('competences.add_qualification', raise_exception=True)
def ajouter_qualification_view(request, licence_id):
    """
    Permet d'ajouter un "diplôme" (une qualification) à une licence existante.
    """
    licence = get_object_or_404(Licence, pk=licence_id)
    
    if request.method == 'POST':
        form = QualificationForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.licence = licence
            instance.save()
            messages.success(request, f"La qualification '{instance.get_type_qualification_display()}' a été ajoutée pour {licence.agent.trigram}.")
            return redirect('competences:dossier_competence', agent_id=licence.agent.id_agent)
    else:
        form = QualificationForm()

    context = {
        'form': form,
        'agent_concerne': licence.agent,
        'titre': f"Ajouter une Qualification pour {licence.agent.trigram}"
    }
    return render(request, 'competences/form_gestion.html', context)

@login_required
@effective_permission_required('competences.change_qualification', raise_exception=True)
def modifier_qualification_view(request, qualification_id):
    """
    Permet de modifier une qualification existante, notamment pour activer/désactiver
    les privilèges pour les rôles optionnels comme ISP ou EXA.
    """
    qualification = get_object_or_404(Qualification, pk=qualification_id)
    licence = qualification.licence
    
    if request.method == 'POST':
        form = QualificationForm(request.POST, instance=qualification)
        if form.is_valid():
            form.save()
            messages.success(request, f"La qualification '{qualification.get_type_qualification_display()}' a été mise à jour.")
            return redirect('competences:dossier_competence', agent_id=licence.agent.id_agent)
    else:
        form = QualificationForm(instance=qualification)

    context = {
        'form': form,
        'agent_concerne': licence.agent,
        'titre': f"Modifier la Qualification '{qualification.get_type_qualification_display()}'"
    }
    return render(request, 'competences/form_gestion.html', context)

@login_required
@effective_permission_required('competences.change_mentionunite', raise_exception=True)
def gerer_mention_unite_view(request, mention_id=None, licence_id=None):
    """
    Gère la création (si mention_id is None) ou la modification
    d'une mention d'unité locale.
    """
    if mention_id:
        mention = get_object_or_404(MentionUnite, pk=mention_id)
        # ### CORRECTION ### : On accède à la licence via le bon chemin
        licence = mention.licence
        titre = f"Modifier la Mention pour {licence.agent.trigram}"
    elif licence_id:
        licence = get_object_or_404(Licence, pk=licence_id)
        mention = None
        titre = f"Ajouter une Mention d'Unité pour {licence.agent.trigram}"
    else:
        return redirect('home')

    if request.method == 'POST':
        form = MentionUniteForm(request.POST, instance=mention, licence=licence)
        if form.is_valid():
            instance = form.save(commit=False)
            if not instance.centre_id:
                 instance.centre = request.centre_agent
            # On lie la mention à la licence si c'est une création
            if not mention_id:
                instance.licence = licence
            instance.save()
            messages.success(request, f"La mention d'unité a été enregistrée avec succès.")
            return redirect('competences:dossier_competence', agent_id=licence.agent.id_agent)
    else:
        form = MentionUniteForm(instance=mention, licence=licence)
    
    context = {
        'form': form,
        'agent_concerne': licence.agent,
        'titre': titre
    }
    return render(request, 'competences/form_gestion.html', context)