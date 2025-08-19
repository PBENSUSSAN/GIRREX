# Fichier : core/views/medical.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from datetime import date

from core.decorators import effective_permission_required
from core.models import Agent, RendezVousMedical
from ..forms import RendezVousMedicalForm, CertificatMedForm

@login_required
# On utilise une permission de 'competences' car la gestion médicale fait partie du suivi de compétence
@effective_permission_required('competences.change_licence', raise_exception=True)
def gerer_rdv_medical_view(request, agent_id, rdv_id=None):
    """
    Gère la création (si rdv_id is None) ou la modification
    d'un rendez-vous médical pour un agent.
    """
    agent = get_object_or_404(Agent, pk=agent_id)
    instance = get_object_or_404(RendezVousMedical, pk=rdv_id) if rdv_id else None

    if request.method == 'POST':
        form = RendezVousMedicalForm(request.POST, instance=instance)
        if form.is_valid():
            rdv = form.save(commit=False)
            rdv.agent = agent
            rdv.save()
            
            action = "modifié" if instance else "planifié"
            messages.success(request, f"Le rendez-vous médical a été {action} avec succès pour {agent.trigram}.")
            return redirect('competences:dossier_competence', agent_id=agent.id_agent)
    else:
        form = RendezVousMedicalForm(instance=instance)

    context = {
        'form': form,
        'agent_concerne': agent,
        'titre': "Gérer un Rendez-vous Médical"
    }
    # On peut réutiliser un template de formulaire générique
    return render(request, 'competences/form_gestion.html', context)

@login_required
@effective_permission_required('competences.change_licence', raise_exception=True)
def enregistrer_resultat_visite_view(request, rdv_id):
    """
    Permet d'enregistrer le résultat (un CertificatMed) d'un RendezVousMedical.
    """
    rdv = get_object_or_404(RendezVousMedical, pk=rdv_id)
    agent = rdv.agent
    
    # On essaie de trouver un certificat déjà lié pour le modifier, sinon on en crée un.
    instance = rdv.certificat_genere

    if request.method == 'POST':
        form = CertificatMedForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            certificat = form.save(commit=False)
            certificat.agent = agent
            certificat.save()
            
            # On lie le certificat au RDV et on marque le RDV comme réalisé
            rdv.certificat_genere = certificat
            rdv.statut = RendezVousMedical.StatutRDV.REALISE
            rdv.save()
            
            messages.success(request, f"Le résultat de la visite médicale pour {agent.trigram} a été enregistré.")
            return redirect('competences:dossier_competence', agent_id=agent.id_agent)
    else:
        # On pré-remplit le formulaire avec les infos du RDV
        initial_data = {
            'date_visite': rdv.date_heure_rdv.date(),
            'organisme_medical': rdv.organisme_medical
        }
        form = CertificatMedForm(instance=instance, initial=initial_data)

    date_visite_formatee = rdv.date_heure_rdv.date().strftime('%d/%m/%Y')
    
    context = {
        'form': form,
        'agent_concerne': agent,
        'titre': f"Saisir Résultat de la Visite du {date_visite_formatee}"
    }
    return render(request, 'competences/form_gestion.html', context)