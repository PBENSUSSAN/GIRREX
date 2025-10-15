# Fichier : activites/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from .models import Vol, SaisieActivite
from .forms import VolCreationForm, VolRealisationForm, SaisieActiviteForm
from core.models import Centre, IndisponibiliteCabine
from django.http import JsonResponse

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

@login_required
# TODO: Ajouter une permission @effective_permission_required("activites.view_planning_cca")
def cca_planning_view(request, date_str):
    """
    Affiche la page squelette de la timeline de planification pour la CCA.
    La logique d'affichage sera ajoutée plus tard.
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        # Gérer le cas où la date dans l'URL est invalide
        return redirect('home') # Ou une page d'erreur

    context = {
        'target_date': target_date,
        'titre': f"Planification CCA - {target_date.strftime('%d %B %Y')}"
    }
    return render(request, 'activites/timeline_cca.html', context)

@login_required
# TODO: Ajouter une permission @effective_permission_required("activites.view_supervision_cca")
def cca_supervision_view(request):
    """
    Affiche la page squelette du "mur d'écrans" de supervision pour la CCA.
    """
    context = {
        'target_date': date.today(),
        'titre': "Supervision du Jour J"
    }
    return render(request, 'activites/supervision_cca.html', context)

@login_required
def api_get_planning_data(request, date_str):
    """
    API qui renvoie les données de planification pour la CCA au format
    attendu par la librairie vis-timeline.
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return JsonResponse({'error': 'Format de date invalide'}, status=400)

    # --- 1. Préparer les GROUPES (les lignes de la timeline : les cabines) ---
    centres_cca = Centre.objects.filter(sous_gestion_cca=True)
    groups = []
    for centre in centres_cca:
        for i in range(1, centre.nombre_cabines + 1):
            cabine_name = f"Cabine {i}"
            groups.append({
                'id': f"{centre.code_centre}_{cabine_name.lower().replace(' ', '')}",
                'content': f"{cabine_name} ({centre.code_centre})"
            })

    # --- 2. Préparer les ITEMS (les blocs de vol et d'indisponibilité) ---
    items = []
    
    # a) Les indisponibilités des cabines
    indisponibilites = IndisponibiliteCabine.objects.filter(date_jour=target_date, centre__in=centres_cca)
    for indispo in indisponibilites:
        # On construit un ID de groupe cohérent
        group_id = f"{indispo.centre.code_centre}_{indispo.nom_cabine.lower().replace(' ', '')}"
        start_datetime = datetime.combine(target_date, indispo.heure_debut)
        end_datetime = datetime.combine(target_date, indispo.heure_fin)
        
        items.append({
            'id': f"indispo_{indispo.id}",
            'group': group_id,
            'content': indispo.motif or "Indisponible",
            'start': start_datetime.isoformat(),
            'end': end_datetime.isoformat(),
            'type': 'background', # Affiche comme une zone non-cliquable
            'style': 'background-color: #f8d7da;', # Style pour les indispos
        })
        
    # b) Les segments de vol déjà planifiés (qui ont un nom de cabine)
    vols_planifies = Vol.objects.filter(
        date_vol=target_date,
        centre__in=centres_cca,
        est_activite_hors_vol=False
    ).exclude(nom_cabine__exact='') # On ne prend que ceux qui sont placés

    for vol in vols_planifies:
        group_id = f"{vol.centre.code_centre}_{vol.nom_cabine.lower().replace(' ', '')}"
        start_datetime = datetime.combine(target_date, vol.heure_debut_prevue)
        end_datetime = start_datetime + vol.duree_prevue

        # Application de la charte graphique via des classes CSS
        className = f"flux-{vol.flux.lower()}" # ex: flux-cam, flux-cag_acs

        items.append({
            'id': vol.id,
            'group': group_id,
            'content': vol.indicatif or vol.numero_strip,
            'start': start_datetime.isoformat(),
            'end': end_datetime.isoformat(),
            'type': 'box', # Un bloc standard
            'className': className,
        })
        
    # --- 3. Préparer les DEMANDES (les vols non encore planifiés - pour plus tard) ---
    # Pour l'instant, on ne les inclut pas dans la réponse à la timeline.
    # On les chargera séparément.

    return JsonResponse({'groups': groups, 'items': items})