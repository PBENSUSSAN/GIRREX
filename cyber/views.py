# Fichier : cyber/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from core.decorators import effective_permission_required
from .models import SMSI, CyberRisque, CyberIncident, CyberRisqueHistorique, CyberIncidentHistorique
from .forms import CyberRisqueForm, CyberIncidentForm
from .audit import log_audit_risque, log_audit_incident
from technique.models import PanneCentre
from .filters import CyberRisqueFilter, CyberIncidentFilter # <-- CORRECTION : CET IMPORT ÉTAIT MANQUANT

# ==============================================================================
# VUE NATIONALE
# ==============================================================================
@login_required
@effective_permission_required('cyber.view_smsi')
def dashboard_national_view(request):
    """ Affiche le tableau de bord national avec les indicateurs clés par centre. """
    
    smsi_list = SMSI.objects.select_related('centre', 'relais_local').annotate(
        risques_ouverts_count=Count('risques', filter=Q(risques__statut='OUVERT')),
        incidents_en_cours_count=Count('incidents', filter=Q(incidents__statut__in=['DETECTION', 'ANALYSE', 'REMEDIATION']))
    ).order_by('centre__code_centre')

    context = {
        'smsi_list': smsi_list,
        'titre': "Tableau de Bord National SMSI"
    }
    return render(request, 'cyber/dashboard_national.html', context)

# ==============================================================================
# VUES LOCALES (PAR CENTRE)
# ==============================================================================
@login_required
@effective_permission_required('cyber.view_smsi')
def smsi_detail_view(request, centre_id):
    """ Affiche le 'poste de pilotage' du SMSI pour un centre donné, avec filtres. """
    smsi = get_object_or_404(SMSI.objects.select_related('centre'), centre_id=centre_id)
    
    risques_qs = CyberRisque.objects.filter(smsi=smsi)
    incidents_qs = CyberIncident.objects.filter(smsi=smsi)

    risque_filter = CyberRisqueFilter(request.GET, queryset=risques_qs, prefix='risk')
    incident_filter = CyberIncidentFilter(request.GET, queryset=incidents_qs, prefix='incident')

    context = {
        'smsi': smsi,
        'risque_filter': risque_filter,
        'incident_filter': incident_filter,
        'titre': f"Dossier de Pilotage SMSI - {smsi.centre.code_centre}"
    }
    
    return render(request, 'cyber/smsi_detail.html', context)

# ==============================================================================
# VUES POUR LA GESTION DES RISQUES
# ==============================================================================
@login_required
@effective_permission_required('cyber.add_cyberrisque')
def creer_risque_view(request, centre_id):
    smsi = get_object_or_404(SMSI, centre_id=centre_id)
    if request.method == 'POST':
        form = CyberRisqueForm(request.POST)
        if form.is_valid():
            risque = form.save(commit=False)
            risque.smsi = smsi
            risque.save()
            log_audit_risque(
                risque=risque,
                type_evenement=CyberRisqueHistorique.TypeEvenement.CREATION,
                auteur=request.user,
                details={'commentaire': form.cleaned_data['commentaire']}
            )
            messages.success(request, "Le risque de cybersécurité a été créé avec succès.")
            return redirect('cyber:detail-risque', risque_id=risque.id)
    else:
        form = CyberRisqueForm()
        
    context = {'form': form, 'smsi': smsi, 'titre': "Déclarer un nouveau risque cyber"}
    return render(request, 'core/form_generique.html', context)

@login_required
@effective_permission_required('cyber.view_cyberrisque')
def detail_risque_view(request, risque_id):
    risque = get_object_or_404(CyberRisque, pk=risque_id)
    historique = risque.historique.all()
    can_edit = request.user.has_perm('cyber.change_cyberrisque')
    
    if request.method == 'POST' and can_edit:
        form = CyberRisqueForm(request.POST, instance=risque)
        if form.is_valid():
            ancien_statut = risque.get_statut_display()
            risque_modifie = form.save()
            log_audit_risque(
                risque=risque_modifie,
                type_evenement=CyberRisqueHistorique.TypeEvenement.MODIFICATION,
                auteur=request.user,
                details={
                    'ancien_statut': ancien_statut,
                    'nouveau_statut': risque_modifie.get_statut_display(),
                    'commentaire': form.cleaned_data['commentaire']
                }
            )
            messages.success(request, "Le risque a été mis à jour.")
            return redirect('cyber:detail-risque', risque_id=risque.id)
    else:
        form = CyberRisqueForm(instance=risque)
        if not can_edit:
            for field in form.fields.values():
                field.disabled = True

    context = {
        'form': form,
        'risque': risque,
        'historique': historique,
        'titre': f"Détail du Risque #{risque.id}",
        'can_edit': can_edit
    }
    return render(request, 'cyber/detail_risque.html', context)

# ==============================================================================
# VUES POUR LA GESTION DES INCIDENTS
# ==============================================================================
@login_required
@effective_permission_required('cyber.add_cyberincident')
def creer_incident_view(request, centre_id):
    smsi = get_object_or_404(SMSI, centre_id=centre_id)
    if request.method == 'POST':
        form = CyberIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.smsi = smsi
            incident.save()
            log_audit_incident(
                incident=incident,
                type_evenement=CyberIncidentHistorique.TypeEvenement.CREATION,
                auteur=request.user,
                details={'commentaire': form.cleaned_data['commentaire']}
            )
            messages.success(request, "L'incident de cybersécurité a été créé avec succès.")
            return redirect('cyber:detail-incident', incident_id=incident.id)
    else:
        form = CyberIncidentForm()

    context = {'form': form, 'smsi': smsi, 'titre': "Déclarer un nouvel incident cyber"}
    return render(request, 'core/form_generique.html', context)

@login_required
@effective_permission_required('cyber.view_cyberincident')
def detail_incident_view(request, incident_id):
    incident = get_object_or_404(CyberIncident, pk=incident_id)
    historique = incident.historique.all()
    can_edit = request.user.has_perm('cyber.change_cyberincident')

    if request.method == 'POST' and can_edit:
        form = CyberIncidentForm(request.POST, instance=incident)
        if form.is_valid():
            ancien_statut = incident.get_statut_display()
            incident_modifie = form.save()
            log_audit_incident(
                incident=incident_modifie,
                type_evenement=CyberIncidentHistorique.TypeEvenement.MODIFICATION,
                auteur=request.user,
                details={
                    'ancien_statut': ancien_statut,
                    'nouveau_statut': incident_modifie.get_statut_display(),
                    'commentaire': form.cleaned_data['commentaire']
                }
            )
            messages.success(request, "L'incident a été mis à jour.")
            return redirect('cyber:detail-incident', incident_id=incident.id)
    else:
        form = CyberIncidentForm(instance=incident)
        if not can_edit:
            for field in form.fields.values():
                field.disabled = True

    context = {
        'form': form,
        'incident': incident,
        'historique': historique,
        'titre': f"Détail de l'Incident #{incident.id}",
        'can_edit': can_edit
    }
    return render(request, 'cyber/detail_incident.html', context)

# ==============================================================================
# PONT DEPUIS LE MODULE TECHNIQUE
# ==============================================================================
@login_required
@effective_permission_required('cyber.add_cyberincident')
def creer_incident_depuis_panne_view(request, panne_id):
    panne = get_object_or_404(PanneCentre, pk=panne_id)
    try:
        smsi = SMSI.objects.get(centre=panne.centre)
    except SMSI.DoesNotExist:
        messages.error(request, f"Aucun dossier de conformité SMSI n'est configuré pour le centre {panne.centre.code_centre}. Veuillez contacter l'administrateur.")
        return redirect('technique:detail-panne', panne_id=panne.id)

    if request.method == 'POST':
        form = CyberIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.smsi = smsi
            incident.source_panne = panne
            incident.save()
            log_audit_incident(
                incident=incident,
                type_evenement=CyberIncidentHistorique.TypeEvenement.QUALIFICATION,
                auteur=request.user,
                details={
                    'commentaire': form.cleaned_data['commentaire'],
                    'source_panne_id': panne.id,
                    'source_panne_desc': str(panne)
                }
            )
            messages.success(request, f"L'incident cyber a été créé et lié à la panne #{panne.id}.")
            return redirect('cyber:detail-incident', incident_id=incident.id)
    else:
        initial_data = {
            'date': panne.date_heure_debut,
            'description': f"Incident qualifié à partir de la panne technique #{panne.id} :\n\n{panne.description}"
        }
        form = CyberIncidentForm(initial=initial_data)
        
    context = {
        'form': form,
        'smsi': smsi,
        'panne_source': panne,
        'titre': "Qualifier une panne en incident cyber"
    }
    return render(request, 'core/form_generique.html', context)