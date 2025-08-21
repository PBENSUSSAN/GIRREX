# Fichier : activites/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from .models import Vol, SaisieActivite
from .forms import VolCreationForm, VolRealisationForm, SaisieActiviteForm
from core.models import Centre

@login_required
def liste_missions_jour_view(request, centre_id, date_str):
    """
    Affiche la liste des MISSIONS (vols parents) pour un jour et un centre donnés.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    target_date = date.fromisoformat(date_str)
    
    # On ne récupère que les vols racines (ceux qui n'ont pas de parent)
    missions = Vol.objects.filter(
        centre=centre, 
        date_vol=target_date,
        parent_vol__isnull=True
    ).prefetch_related('releves')

    context = {
        'centre': centre,
        'target_date': target_date,
        'missions': missions,
        'vol_form': VolCreationForm(initial={'date_vol': target_date})
    }
    return render(request, 'activites/saisie_jour.html', context)

@login_required
def ajouter_mission_view(request, centre_id):
    """
    Traite le formulaire de création d'une nouvelle mission (vol parent).
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    date_str = date.today().isoformat()

    if request.method == 'POST':
        form = VolCreationForm(request.POST)
        if form.is_valid():
            mission = form.save(commit=False)
            mission.centre = centre
            mission.save()
            date_str = mission.date_vol.isoformat()
            messages.success(request, f"La mission {mission.indicatif} a été planifiée.")
            # On redirige vers la page de détail de la nouvelle mission
            return redirect('activites:detail_mission', mission_id=mission.id)
    
    # Si le formulaire n'est pas valide, on retourne à la liste
    messages.error(request, "Erreur dans le formulaire de création de mission.")
    return redirect('activites:saisie_jour', centre_id=centre.id, date_str=date_str)

@login_required
def detail_mission_view(request, mission_id):
    mission = get_object_or_404(Vol, pk=mission_id, parent_vol__isnull=True)
    segments = [mission] + list(mission.releves.all().order_by('heure_debut_prevue'))

    for segment in segments:
        segment.get_realisation_form = VolRealisationForm(instance=segment)
        # On passe le segment au constructeur du formulaire
        segment.get_activite_form = SaisieActiviteForm(vol=segment)

    context = {
        'mission': mission,
        'segments': segments,
    }
    return render(request, 'activites/detail_mission.html', context)

@login_required
def ajouter_releve_view(request, mission_id):
    """
    Crée une nouvelle relève (un nouveau segment de vol) pour une mission existante.
    """
    mission = get_object_or_404(Vol, pk=mission_id, parent_vol__isnull=True)
    
    # Trouver le dernier segment pour pré-remplir l'heure de début
    dernier_segment = mission.releves.order_by('-heure_debut_prevue').first() or mission

    # Création de la relève
    Vol.objects.create(
        parent_vol=mission,
        centre=mission.centre,
        date_vol=mission.date_vol,
        flux=mission.flux,
        numero_strip=mission.numero_strip,
        numero_commande=mission.numero_commande,
        indicatif=mission.indicatif,
        heure_debut_prevue=dernier_segment.heure_fin_reelle or dernier_segment.heure_debut_prevue,
        duree_prevue=mission.duree_prevue,
    )
    messages.success(request, "Une nouvelle relève a été ajoutée à la mission.")
    return redirect('activites:detail_mission', mission_id=mission.id)

@login_required
def ajouter_participant_view(request, segment_id):
    segment = get_object_or_404(Vol, pk=segment_id)
    mission_id = segment.parent_vol.id if segment.parent_vol else segment.id

    if request.method == 'POST':
        # On passe le segment au constructeur du formulaire
        form = SaisieActiviteForm(request.POST, vol=segment)
        if form.is_valid():
            # Si le formulaire est valide, toutes les vérifications ont déjà été faites !
            activite = form.save(commit=False)
            activite.vol = segment
            activite.save()
            messages.success(request, f"Participant ajouté avec succès au segment.")
        else:
            # On affiche les erreurs de validation claires du formulaire
            messages.error(request, f"Erreur de validation : {form.errors.as_text()}")

    return redirect('activites:detail_mission', mission_id=mission_id)

@login_required
def supprimer_participant_view(request, activite_id):
    """ Supprime un participant d'un segment de vol. """
    activite = get_object_or_404(SaisieActivite.objects.select_related('vol'), pk=activite_id)
    segment = activite.vol
    mission_id = segment.parent_vol.id if segment.parent_vol else segment.id
    
    activite.delete()
    messages.info(request, "Le participant a été retiré du segment.")
    return redirect('activites:detail_mission', mission_id=mission_id)

@login_required
def saisir_heures_reelles_view(request, segment_id):
    """
    Traite la saisie des heures réelles pour un segment de vol spécifique.
    """
    segment = get_object_or_404(Vol, pk=segment_id)
    mission_id = segment.parent_vol.id if segment.parent_vol else segment.id

    if request.method == 'POST':
        form = VolRealisationForm(request.POST, instance=segment)
        if form.is_valid():
            form.save()
            messages.success(request, "Les heures réelles du segment ont été mises à jour.")
        else:
            messages.error(request, "Erreur dans le formulaire des heures réelles.")

    return redirect('activites:detail_mission', mission_id=mission_id)