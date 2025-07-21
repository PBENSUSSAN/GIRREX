# ==============================================================================
# Fichier : core/views.py (VERSION FINALE ET COMPLÈTE)
# ==============================================================================

import calendar
import json
from datetime import date, timedelta
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Agent, PositionJour, TourDeService, Centre, VersionTourDeService
from .decorators import effective_permission_required

# --- VUES EXISTANTES ---
@login_required
def home(request):
    context = {} 
    return render(request, 'core/home.html', context)

@effective_permission_required('core.view_agent')
def liste_agents(request):
    agents = Agent.objects.all().order_by('reference')
    context = {'agents': agents}
    return render(request, 'core/liste_agents.html', context)

# --- NOUVELLE LOGIQUE POUR LE TOUR DE SERVICE ---
@login_required
def selecteur_centre_view(request):
    try:
        user_centre = request.user.agent_profile.centre
        if user_centre:
            return redirect('tour-de-service-centre', centre_id=user_centre.id)
    except AttributeError:
        pass

    centres = Centre.objects.all()
    context = {'centres': centres}
    return render(request, 'core/selecteur_centre.html', context)


@login_required
def tour_de_service_view(request, centre_id, year=None, month=None):
    centre = get_object_or_404(Centre, pk=centre_id)
    today = date.today()
    if year is None: year = today.year
    if month is None: month = today.month
    
    current_month_date = date(year, month, 1)
    prev_month_date = (current_month_date - timedelta(days=1)).replace(day=1)
    next_month_date = (current_month_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    agents_du_centre = Agent.objects.filter(centre=centre, actif=True).order_by('trigram')
    positions_du_centre = PositionJour.objects.filter(centre=centre)
    
    cal = calendar.Calendar()
    days_in_month = [d for d in cal.itermonthdates(year, month) if d.month == month]

    tours = TourDeService.objects.filter(agent__in=agents_du_centre, date__range=(days_in_month[0], days_in_month[-1])).select_related('position_matin', 'position_apres_midi')
    
    planning_data = {agent.id_agent: {} for agent in agents_du_centre}
    for tour in tours:
        planning_data[tour.agent_id][tour.date] = tour
        
    planning_json_data = {}
    for tour in tours:
        agent_id_key = tour.agent_id
        date_key = tour.date.isoformat()
        if agent_id_key not in planning_json_data:
            planning_json_data[agent_id_key] = {}
        planning_json_data[agent_id_key][date_key] = {
            'position_matin_id': tour.position_matin_id, 'position_matin_nom': tour.position_matin.nom if tour.position_matin else "",
            'position_apres_midi_id': tour.position_apres_midi_id, 'position_apres_midi_nom': tour.position_apres_midi.nom if tour.position_apres_midi else "",
            'commentaire': tour.commentaire or ""
        }

    jours_fr = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
    days_formatted_for_template = [{"date": d, "jour_court": jours_fr[d.weekday()], "num": d.day} for d in days_in_month]
    days_formatted_for_json = [{"date_iso": d.isoformat(), "jour_court": jours_fr[d.weekday()], "num": d.day, "weekday": d.weekday()} for d in days_in_month]

    context = {
        'centre': centre,
        'user_can_edit': request.user.has_perm('core.change_tourdeservice'),
        'current_month_display': current_month_date.strftime('%B %Y').capitalize(),
        'current_year': year,
        'current_month': month,
        
        'agents': agents_du_centre,
        'days_in_month_formatted': days_formatted_for_template,
        'planning_data': planning_data,
        
        'agents_json': json.dumps(list(agents_du_centre.values('id_agent', 'trigram', 'reference')), cls=DjangoJSONEncoder),
        'days_json': json.dumps(days_formatted_for_json, cls=DjangoJSONEncoder),
        'planning_json': json.dumps(planning_json_data, cls=DjangoJSONEncoder),
        'positions_json': json.dumps(list(positions_du_centre.values('id', 'nom')), cls=DjangoJSONEncoder),

        'prev_month_url': reverse('tour-de-service-monthly', args=[centre.id, prev_month_date.year, prev_month_date.month]),
        'next_month_url': reverse('tour-de-service-monthly', args=[centre.id, next_month_date.year, next_month_date.month]),
    }
    return render(request, 'core/tour_de_service.html', context)

# --- VUES AJAX ET API ---
@require_POST
@login_required
@permission_required('core.change_tourdeservice', raise_exception=True)
def update_tour_de_service(request):
    data = json.loads(request.body)
    try:
        position_matin_id = data.get('position_matin_id')
        position_aprem_id = data.get('position_apres_midi_id')
        if not position_aprem_id:
            position_aprem_id = position_matin_id
        tour, created = TourDeService.objects.update_or_create(
            agent_id=data.get('agent_id'),
            date=date.fromisoformat(data.get('date')),
            defaults={'position_matin_id': position_matin_id, 'position_apres_midi_id': position_aprem_id, 'modifie_par': request.user}
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@login_required
@permission_required('core.change_tourdeservice', raise_exception=True)
def update_tour_de_service_comment(request):
    data = json.loads(request.body)
    try:
        tour, created = TourDeService.objects.get_or_create(
            agent_id=data.get('agent_id'),
            date=date.fromisoformat(data.get('date')),
            defaults={'modifie_par': request.user}
        )
        tour.commentaire = data.get('commentaire', '')
        tour.modifie_par = request.user
        tour.save()
        return JsonResponse({'status': 'ok', 'comment_exists': bool(tour.commentaire)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@permission_required('core.view_positionjour', raise_exception=True)
def api_get_positions(request, centre_id):
    positions = PositionJour.objects.filter(centre_id=centre_id).values('id', 'nom', 'description', 'categorie')
    return JsonResponse(list(positions), safe=False)

@require_POST
@login_required
@permission_required('core.add_positionjour', raise_exception=True)
def api_add_position(request, centre_id):
    data = json.loads(request.body)
    try:
        position = PositionJour.objects.create(
            centre_id=centre_id,
            nom=data.get('nom'),
            description=data.get('description'),
            categorie=data.get('categorie')
        )
        return JsonResponse({'status': 'ok', 'id': position.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@login_required
@permission_required('core.change_positionjour', raise_exception=True)
def api_update_position(request, position_id):
    data = json.loads(request.body)
    try:
        position = PositionJour.objects.get(pk=position_id)
        position.nom = data.get('nom', position.nom)
        position.description = data.get('description', position.description)
        position.categorie = data.get('categorie', position.categorie)
        position.save()
        return JsonResponse({'status': 'ok'})
    except PositionJour.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Position non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@login_required
@permission_required('core.delete_positionjour', raise_exception=True)
def api_delete_position(request, position_id):
    try:
        position = PositionJour.objects.get(pk=position_id)
        position.delete()
        return JsonResponse({'status': 'ok'})
    except PositionJour.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Position non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@login_required
@permission_required('core.add_versiontourdeservice', raise_exception=True)
def valider_tour_de_service(request, centre_id, year, month):
    centre = get_object_or_404(Centre, pk=centre_id)
    
    with transaction.atomic():
        # 1. On récupère les données du planning "live"
        agents_du_centre = Agent.objects.filter(centre=centre, actif=True)
        premier_jour = date(int(year), int(month), 1)
        dernier_jour = premier_jour.replace(day=calendar.monthrange(int(year), int(month))[1])

        tours = TourDeService.objects.filter(
            agent__in=agents_du_centre,
            date__range=(premier_jour, dernier_jour)
        ).select_related('agent', 'position_matin', 'position_apres_midi')

        planning_snapshot = {}
        for tour in tours:
            agent_key = str(tour.agent.id_agent)
            if agent_key not in planning_snapshot:
                planning_snapshot[agent_key] = {
                    'trigram': tour.agent.trigram or tour.agent.reference,
                    'planning': {}
                }
            
            planning_snapshot[agent_key]['planning'][tour.date.isoformat()] = {
                'position_matin': tour.position_matin.nom if tour.position_matin else None,
                'position_apres_midi': tour.position_apres_midi.nom if tour.position_apres_midi else None,
                'commentaire': tour.commentaire
            }
            
        # 2. On calcule le nouveau numéro de version
        versions_existantes = VersionTourDeService.objects.filter(
            centre=centre, annee=year, mois=month
        ).count()
        nouveau_numero_index = versions_existantes + 1
        
        # Formatage du numéro (ex: "072025-1")
        numero_version_str = f"{str(month).zfill(2)}{year}-{nouveau_numero_index}"

        # 3. On CRÉE la nouvelle version avec son numéro
        VersionTourDeService.objects.create(
            centre=centre,
            annee=year,
            mois=month,
            numero_version=numero_version_str, # On enregistre le nouveau numéro
            valide_par=request.user,
            donnees_planning=planning_snapshot
        )
    
    return JsonResponse({'status': 'ok', 'message': "Une nouvelle version du planning a été sauvegardée."})

# --- VUES POUR LA CONSULTATION DES VERSIONS VALIDÉES ---
@login_required
def liste_versions_validees(request, centre_id):
    centre = get_object_or_404(Centre, pk=centre_id)
    versions = VersionTourDeService.objects.filter(centre=centre).order_by('-date_validation')
    
    context = {
        'centre': centre,
        'versions': versions
    }
    return render(request, 'core/liste_versions.html', context)

@login_required
def voir_version_validee(request, version_id):
    version = get_object_or_404(VersionTourDeService, pk=version_id)
    planning_data = version.donnees_planning
    
    agents_dans_version = sorted(planning_data.keys(), key=lambda k: planning_data[k]['trigram'])
    
    premier_jour = date(version.annee, version.mois, 1)
    cal = calendar.Calendar()
    days_in_month = [d for d in cal.itermonthdates(version.annee, version.mois) if d.month == version.mois]

    jours_fr = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
    days_formatted = [{"date": d, "jour_court": jours_fr[d.weekday()], "num": d.day} for d in days_in_month]
    
    context = {
        'version': version,
        'centre': version.centre,
        'agents': agents_dans_version,
        'days_in_month_formatted': days_formatted,
        'planning_data': planning_data
    }
    return render(request, 'core/voir_version.html', context)