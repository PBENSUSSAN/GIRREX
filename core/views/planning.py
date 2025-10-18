# ==============================================================================
# Fichier : core/views/planning.py
# Vues et API pour le module "Tour de Service" (Planning).
# ==============================================================================

# --- Imports Standards & Django ---
import calendar
import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages

# --- Imports Locaux (de votre application) ---
from ..models import (
    Agent, Centre, PositionJour, TourDeService, VersionTourDeService,IndisponibiliteCabine
)
from ..forms import IndisponibiliteCabineForm


@login_required
def tour_de_service_view(request, centre_id, year=None, month=None):
    """ 
    Sert la page squelette HTML pour le planning du Tour de Service.
    
    ⚠️ SÉCURITÉ : Vérifie que l'utilisateur a le droit de voir CE centre.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    
    # ✅ CONTRÔLE DE SÉCURITÉ
    if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Vous devez être un agent pour accéder au planning.")
    
    agent = request.user.agent_profile
    
    # Vérifier si l'utilisateur peut accéder à CE centre
    from core.models import Role
    from django.core.exceptions import PermissionDenied
    
    acces_autorise = False
    
    # 1. Vision NATIONALE (Chef Division, Adjoint Chef Division, Adjoint Form)
    if request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_FORM
    ]:
        acces_autorise = True
    
    # 2. Permission view_all_licences
    elif 'competences.view_all_licences' in request.effective_perms:
        acces_autorise = True
    
    # 3. Chef de Centre / Adjoint / FORM_LOCAL de CE centre uniquement
    elif request.centre_agent and request.centre_agent.id == centre.id:
        acces_autorise = True
    
    # ✅ BLOQUER SI PAS D'ACCÈS
    if not acces_autorise:
        raise PermissionDenied(
            f"Vous n'avez pas l'autorisation d'accéder au planning du centre {centre.code_centre}. "
            f"Vous ne pouvez voir que le planning de votre propre centre."
        )
    
    today = date.today()
    year = year or today.year
    month = month or today.month
    
    current_month_date = date(year, month, 1)
    prev_month_date = (current_month_date - timedelta(days=1)).replace(day=1)
    next_month_date = (current_month_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    # ✅ NOUVEAU : Récupérer l'arrêt à traiter depuis la session
    arret_a_traiter = request.session.get('arret_a_traiter', None)
    
    # Si l'arrêt est pour un autre centre, ignorer
    if arret_a_traiter:
        try:
            from core.models import Agent
            agent = Agent.objects.get(pk=arret_a_traiter['agent_id'])
            if agent.centre.id != centre.id:
                arret_a_traiter = None
        except:
            arret_a_traiter = None

    context = {
        'centre': centre,
        'user_can_edit': request.user.has_perm('core.change_tourdeservice'),
        'current_month_display': current_month_date.strftime('%B %Y').capitalize(),
        'current_year': year,
        'current_month': month,
        'prev_month_url': reverse('tour-de-service-monthly', args=[centre.id, prev_month_date.year, prev_month_date.month]),
        'next_month_url': reverse('tour-de-service-monthly', args=[centre.id, next_month_date.year, next_month_date.month]),
        'arret_a_traiter': arret_a_traiter,  # ✅ Passer au template
    }
    
    # ✅ FIX : Rendre le template D'ABORD
    response = render(request, 'core/tour_de_service.html', context)
    
    # ✅ Nettoyer la session APRÈS le rendu
    if arret_a_traiter and 'arret_a_traiter' in request.session:
        del request.session['arret_a_traiter']
    
    return response


@login_required
def api_get_planning_data(request, centre_id, year, month):
    """ API qui renvoie les données du planning (agents, jours, affectations) en JSON. """
    centre = get_object_or_404(Centre, pk=centre_id)
    agents_du_centre = Agent.objects.filter(centre=centre, actif=True).order_by('trigram')
    cal = calendar.Calendar()
    days_in_month = [d for d in cal.itermonthdates(year, month) if d.month == month]

    # ✅ Récupérer les tours pour les AGENTS
    tours = TourDeService.objects.filter(
        agent__in=agents_du_centre, 
        date__range=(days_in_month[0], days_in_month[-1])
    ).select_related('position_matin', 'position_apres_midi')
    
    planning_data = {}
    for tour in tours:
        agent_id_key = tour.agent_id; date_key = tour.date.isoformat()
        if agent_id_key not in planning_data: planning_data[agent_id_key] = {}
        planning_data[agent_id_key][date_key] = {
            'position_matin_id': tour.position_matin_id,
            'position_matin_nom': tour.position_matin.nom if tour.position_matin else "",
            'position_apres_midi_id': tour.position_apres_midi_id,
            'position_apres_midi_nom': tour.position_apres_midi.nom if tour.position_apres_midi else "",
            'commentaire': tour.commentaire or ""
        }

    # ✅ NOUVEAU : Récupérer les commentaires JOUR (agent_id=NULL)
    commentaires_jour = TourDeService.objects.filter(
        agent_id__isnull=True,
        date__range=(days_in_month[0], days_in_month[-1])
    ).values('date', 'commentaire')
    
    # Créer un dictionnaire {date_iso: commentaire}
    day_comments = {}
    for comment in commentaires_jour:
        if comment['commentaire']:  # Seulement si commentaire non vide
            day_comments[comment['date'].isoformat()] = comment['commentaire']

    jours_fr = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
    days_formatted = [
        {
            "date_iso": d.isoformat(), 
            "jour_court": jours_fr[d.weekday()], 
            "num": d.day, 
            "weekday": d.weekday(),
            "commentaire_jour": day_comments.get(d.isoformat(), "")  # ✅ NOUVEAU
        } 
        for d in days_in_month
    ]

    return JsonResponse({
        'agents': list(agents_du_centre.values('id_agent', 'trigram', 'reference')), 
        'days': days_formatted, 
        'planning_data': planning_data
    })


@require_POST
@login_required
@permission_required('core.change_tourdeservice', raise_exception=True)
def update_tour_de_service(request):
    """ API pour mettre à jour une cellule du planning. """
    data = json.loads(request.body)
    try:
        position_matin_id = data.get('position_matin_id')
        position_aprem_id = data.get('position_apres_midi_id')
        if not position_aprem_id: position_aprem_id = position_matin_id
        
        TourDeService.objects.update_or_create(
            agent_id=data.get('agent_id'), date=date.fromisoformat(data.get('date')),
            defaults={'position_matin_id': position_matin_id, 'position_apres_midi_id': position_aprem_id, 'modifie_par': request.user}
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
@login_required
@permission_required('core.change_tourdeservice', raise_exception=True)
def update_tour_de_service_comment(request):
    """ 
    API pour mettre à jour le commentaire d'une cellule du planning.
    
    ✅ NOUVEAU : Supporte agent_id=null pour les commentaires JOUR (pas liés à un agent)
    """
    data = json.loads(request.body)
    try:
        agent_id = data.get('agent_id')  # Peut être null pour commentaire jour
        date_str = data.get('date')
        commentaire_text = data.get('commentaire', '')
        
        # ✅ Si agent_id est null, c'est un commentaire JOUR
        if agent_id is None:
            tour, created = TourDeService.objects.get_or_create(
                agent_id=None,  # Commentaire pour la journée
                date=date.fromisoformat(date_str),
                defaults={'modifie_par': request.user}
            )
        else:
            # Commentaire pour un agent spécifique (comportement existant)
            tour, created = TourDeService.objects.get_or_create(
                agent_id=agent_id,
                date=date.fromisoformat(date_str),
                defaults={'modifie_par': request.user}
            )
        
        tour.commentaire = commentaire_text
        tour.modifie_par = request.user
        tour.save()
        
        return JsonResponse({'status': 'ok', 'comment_exists': bool(tour.commentaire)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@permission_required('core.view_positionjour', raise_exception=True)
def api_get_positions(request, centre_id):
    """ API pour lister les positions d'un centre (utilisée par la modale de config). """
    positions = PositionJour.objects.filter(centre_id=centre_id).values('id', 'nom', 'description', 'categorie', 'couleur')
    return JsonResponse(list(positions), safe=False)


@require_POST
@login_required
@permission_required('core.add_positionjour', raise_exception=True)
def api_add_position(request, centre_id):
    """ API pour ajouter une nouvelle position. """
    data = json.loads(request.body)
    try:
        position = PositionJour.objects.create(centre_id=centre_id, nom=data.get('nom'), description=data.get('description'), categorie=data.get('categorie'), couleur=data.get('couleur', '#FFFFFF'))
        return JsonResponse({'status': 'ok', 'id': position.id})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
@login_required
@permission_required('core.change_positionjour', raise_exception=True)
def api_update_position(request, position_id):
    """ API pour modifier une position existante. """
    data = json.loads(request.body)
    try:
        position = PositionJour.objects.get(pk=position_id)
        position.nom = data.get('nom', position.nom); position.description = data.get('description', position.description); position.categorie = data.get('categorie', position.categorie); position.couleur = data.get('couleur', position.couleur); position.save()
        return JsonResponse({'status': 'ok'})
    except PositionJour.DoesNotExist: return JsonResponse({'status': 'error', 'message': 'Position non trouvée'}, status=404)
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
@login_required
@permission_required('core.delete_positionjour', raise_exception=True)
def api_delete_position(request, position_id):
    """ API pour supprimer une position. """
    try:
        PositionJour.objects.get(pk=position_id).delete()
        return JsonResponse({'status': 'ok'})
    except PositionJour.DoesNotExist: return JsonResponse({'status': 'error', 'message': 'Position non trouvée'}, status=404)
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
@login_required
@permission_required('core.add_versiontourdeservice', raise_exception=True)
def valider_tour_de_service(request, centre_id, year, month):
    """ Crée un 'snapshot' validé du planning du mois courant. """
    centre = get_object_or_404(Centre, pk=centre_id)
    with transaction.atomic():
        agents_du_centre = Agent.objects.filter(centre=centre, actif=True)
        premier_jour = date(int(year), int(month), 1)
        dernier_jour = premier_jour.replace(day=calendar.monthrange(int(year), int(month))[1])
        
        # ✅ Récupérer les tours AGENTS
        tours = TourDeService.objects.filter(
            agent__in=agents_du_centre, 
            date__range=(premier_jour, dernier_jour)
        ).select_related('agent', 'position_matin', 'position_apres_midi')
        
        planning_snapshot = {}
        for tour in tours:
            agent_key = str(tour.agent.id_agent)
            if agent_key not in planning_snapshot:
                planning_snapshot[agent_key] = {'trigram': tour.agent.trigram or tour.agent.reference, 'planning': {}}
            planning_snapshot[agent_key]['planning'][tour.date.isoformat()] = {
                'position_matin': tour.position_matin.nom if tour.position_matin else None,
                'position_matin_couleur': tour.position_matin.couleur if tour.position_matin else None,
                'position_apres_midi': tour.position_apres_midi.nom if tour.position_apres_midi else None,
                'position_apres_midi_couleur': tour.position_apres_midi.couleur if tour.position_apres_midi else None,
                'commentaire': tour.commentaire
            }
        
        # ✅ NOUVEAU : Récupérer les commentaires JOUR
        commentaires_jour = TourDeService.objects.filter(
            agent_id__isnull=True,
            date__range=(premier_jour, dernier_jour)
        ).values('date', 'commentaire')
        
        # Créer un dictionnaire des commentaires jour
        day_comments = {}
        for comment in commentaires_jour:
            if comment['commentaire']:
                day_comments[comment['date'].isoformat()] = comment['commentaire']
        
        # Ajouter les commentaires jour au snapshot
        if day_comments:
            planning_snapshot['commentaires_jour'] = day_comments  # ✅ Sans underscore
        
        versions_existantes = VersionTourDeService.objects.filter(centre=centre, annee=year, mois=month).count()
        nouveau_numero_index = versions_existantes + 1
        numero_version_str = f"{str(month).zfill(2)}{year}-{nouveau_numero_index}"
        VersionTourDeService.objects.create(
            centre=centre, 
            annee=year, 
            mois=month, 
            numero_version=numero_version_str, 
            valide_par=request.user, 
            donnees_planning=planning_snapshot
        )
    return JsonResponse({'status': 'ok', 'message': "Une nouvelle version du planning a été sauvegardée."})


@login_required
def liste_versions_validees(request, centre_id):
    """ Affiche l'historique des versions de planning validées. """
    centre = get_object_or_404(Centre, pk=centre_id)
    versions = VersionTourDeService.objects.filter(centre=centre).order_by('-date_validation')
    context = {'centre': centre, 'versions': versions}
    return render(request, 'core/liste_versions.html', context)


@login_required
def voir_version_validee(request, version_id):
    """ Affiche le contenu d'une version de planning archivée. """
    version = get_object_or_404(VersionTourDeService, pk=version_id)
    planning_data = version.donnees_planning
    cal = calendar.Calendar()
    days_in_month = [d for d in cal.itermonthdates(version.annee, version.mois) if d.month == version.mois]
    jours_fr = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
    days_formatted = [{"date": d, "jour_court": jours_fr[d.weekday()], "num": d.day} for d in days_in_month]
    context = { 'version': version, 'centre': version.centre, 'days_in_month_formatted': days_formatted, 'planning_data': planning_data }
    return render(request, 'core/voir_version.html', context)

@login_required
# Il faudra une permission, par ex: '@effective_permission_required("core.change_centre")'
def gestion_capacite_view(request, centre_id):
    """
    Affiche la liste des indisponibilités pour un centre et permet d'en ajouter.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    
    if request.method == 'POST':
        form = IndisponibiliteCabineForm(request.POST)
        if form.is_valid():
            indispo = form.save(commit=False)
            indispo.centre = centre
            indispo.save()
            messages.success(request, "La période d'indisponibilité a été enregistrée.")
            return redirect('gestion_capacite', centre_id=centre.id)
    else:
        form = IndisponibiliteCabineForm(initial={'date_jour': date.today()})

    indisponibilites = IndisponibiliteCabine.objects.filter(
        centre=centre, 
        date_jour__gte=date.today()
    ).order_by('date_jour', 'heure_debut')

    context = {
        'centre': centre,
        'form': form,
        'indisponibilites': indisponibilites,
        'titre': f"Gestion de la Capacité - {centre.code_centre}"
    }
    return render(request, 'core/gestion_capacite.html', context)