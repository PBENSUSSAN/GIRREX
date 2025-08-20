# Fichier : competences/views/gestion.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from core.decorators import effective_permission_required
from core.models import Agent
from ..models import Licence, Qualification, MentionUnite, HistoriqueCompetence
from ..forms import LicenceForm, QualificationForm, MentionUniteForm, ReactiverLicenceForm


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
        licence = mention.licence
        titre = f"Modifier la Mention pour {licence.agent.trigram}"
    elif licence_id:
        licence = get_object_or_404(Licence, pk=licence_id)
        mention = None
        titre = f"Ajouter une Mention d'Unité pour {licence.agent.trigram}"
    else:
        # Si aucun identifiant n'est fourni, on ne peut rien faire.
        return redirect('home')

    if request.method == 'POST':
        form = MentionUniteForm(request.POST, instance=mention, licence=licence)
        if form.is_valid():
            instance = form.save(commit=False)

            # On lie la mention à la licence si c'est une création
            if not mention_id:
                instance.licence = licence

            # ==========================================================
            #                      CORRECTION
            # ==========================================================
            # On récupère le centre directement depuis l'agent associé à la licence.
            # C'est la source de vérité la plus fiable.
            agent_concerne = licence.agent
            
            # On vérifie que cet agent a bien un centre de défini.
            if agent_concerne.centre:
                # Si oui, on l'assigne à notre nouvelle mention.
                instance.centre = agent_concerne.centre
            else:
                # Si l'agent n'a pas de centre, on bloque la création
                # et on envoie un message d'erreur clair à l'utilisateur.
                messages.error(request, f"Opération impossible : l'agent {agent_concerne.trigram} n'est rattaché à aucun centre.")
                context = { 'form': form, 'agent_concerne': licence.agent, 'titre': titre }
                return render(request, 'competences/form_gestion.html', context)
            # ==========================================================
            #                   FIN DE LA CORRECTION
            # ==========================================================
            
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

def reactiver_licence_view(request, licence_id):
    """
    Permet à un responsable de repasser une licence au statut 'Valide'.
    """
    licence = get_object_or_404(Licence, pk=licence_id)
    
    if request.method == 'POST':
        form = ReactiverLicenceForm(request.POST)
        if form.is_valid():
            # Mise à jour de la licence
            licence.statut = Licence.Statut.VALIDE
            licence.motif_inaptitude = None
            licence.date_debut_inaptitude = None
            licence.save()
            
            # Création de l'entrée dans le journal d'audit
            HistoriqueCompetence.objects.create(
                licence=licence,
                type_evenement=HistoriqueCompetence.TypeEvenement.STATUT_LICENCE_CHANGE,
                details={
                    'message': f"Licence réactivée par {request.user.username}. Justification : {form.cleaned_data['commentaire']}"
                }
            )
            
            messages.success(request, f"La licence de {licence.agent.trigram} a été réactivée avec succès.")
            return redirect('competences:dossier_competence', agent_id=licence.agent.id_agent)
    else:
        form = ReactiverLicenceForm()

    context = {
        'form': form,
        'agent_concerne': licence.agent,
        'licence': licence,
        'titre': f"Réactiver la Licence de {licence.agent.trigram}"
    }
    return render(request, 'competences/form_gestion.html', context) # On réutilise le même template de formulaire