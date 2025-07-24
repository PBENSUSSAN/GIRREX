# ==============================================================================
# Fichier : core/views.py (VERSION FINALE, INTÉGRALE ET NETTOYÉE)
# ==============================================================================

# --- Imports Standards & Django ---
import calendar
import json
from datetime import date, timedelta, datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

# --- Imports Locaux (de votre application) ---
from .decorators import effective_permission_required
from .models import (
    Agent, Centre, FeuilleTempsEntree, FeuilleTempsVerrou, FeuilleTempsCloture,
    PositionJour, TourDeService, VersionTourDeService
)
from .services import verifier_regles_horaires


# ==============================================================================
# SECTION I : VUES GÉNÉRALES
# ==============================================================================

@login_required
def home(request):
    """ Affiche la page d'accueil / le tableau de bord. """
    context = {} 
    return render(request, 'core/home.html', context)

@effective_permission_required('core.view_agent')
def liste_agents(request):
    """ Affiche la liste de tous les agents. """
    agents = Agent.objects.all().order_by('reference')
    context = {'agents': agents}
    return render(request, 'core/liste_agents.html', context)

# ==============================================================================
# SECTION II : LOGIQUE DU TOUR DE SERVICE (PLANNING)
# ==============================================================================

@login_required
def selecteur_centre_view(request):
    """ Permet à un utilisateur de choisir un centre pour les modules associés. """
    try:
        user_centre = request.user.agent_profile.centre
        if user_centre:
            return redirect('tour-de-service-centre', centre_id=user_centre.id)
    except (AttributeError, Agent.agent_profile.RelatedObjectDoesNotExist):
        pass
    centres = Centre.objects.all()
    context = {'centres': centres}
    return render(request, 'core/selecteur_centre.html', context)

@login_required
def tour_de_service_view(request, centre_id, year=None, month=None):
    """ Sert la page squelette HTML pour le planning du Tour de Service. """
    centre = get_object_or_404(Centre, pk=centre_id)
    today = date.today()
    year = year or today.year
    month = month or today.month
    
    current_month_date = date(year, month, 1)
    prev_month_date = (current_month_date - timedelta(days=1)).replace(day=1)
    next_month_date = (current_month_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    context = {
        'centre': centre,
        'user_can_edit': request.user.has_perm('core.change_tourdeservice'),
        'current_month_display': current_month_date.strftime('%B %Y').capitalize(),
        'current_year': year,
        'current_month': month,
        'prev_month_url': reverse('tour-de-service-monthly', args=[centre.id, prev_month_date.year, prev_month_date.month]),
        'next_month_url': reverse('tour-de-service-monthly', args=[centre.id, next_month_date.year, next_month_date.month]),
    }
    return render(request, 'core/tour_de_service.html', context)

# ==============================================================================
# SECTION III : API & VUES AJAX (POUR LE TOUR DE SERVICE)
# ==============================================================================

@login_required
def api_get_planning_data(request, centre_id, year, month):
    """ API qui renvoie les données du planning (agents, jours, affectations) en JSON. """
    centre = get_object_or_404(Centre, pk=centre_id)
    agents_du_centre = Agent.objects.filter(centre=centre, actif=True).order_by('trigram')
    cal = calendar.Calendar()
    days_in_month = [d for d in cal.itermonthdates(year, month) if d.month == month]

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

    jours_fr = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
    days_formatted = [{"date_iso": d.isoformat(), "jour_court": jours_fr[d.weekday()], "num": d.day, "weekday": d.weekday()} for d in days_in_month]

    return JsonResponse({'agents': list(agents_du_centre.values('id_agent', 'trigram', 'reference')), 'days': days_formatted, 'planning_data': planning_data})

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
    """ API pour mettre à jour le commentaire d'une cellule du planning. """
    data = json.loads(request.body)
    try:
        tour, created = TourDeService.objects.get_or_create(
            agent_id=data.get('agent_id'), date=date.fromisoformat(data.get('date')),
            defaults={'modifie_par': request.user}
        )
        tour.commentaire = data.get('commentaire', ''); tour.modifie_par = request.user; tour.save()
        return JsonResponse({'status': 'ok', 'comment_exists': bool(tour.commentaire)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# ==============================================================================
# SECTION IV : API POUR LA GESTION DES POSITIONS
# ==============================================================================

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

# ==============================================================================
# SECTION V : GESTION DES VERSIONS DU TDS
# ==============================================================================

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
        tours = TourDeService.objects.filter(agent__in=agents_du_centre, date__range=(premier_jour, dernier_jour)).select_related('agent', 'position_matin', 'position_apres_midi')
        planning_snapshot = {}
        for tour in tours:
            agent_key = str(tour.agent.id_agent)
            if agent_key not in planning_snapshot:
                planning_snapshot[agent_key] = {'trigram': tour.agent.trigram or tour.agent.reference, 'planning': {}}
            planning_snapshot[agent_key]['planning'][tour.date.isoformat()] = {'position_matin': tour.position_matin.nom if tour.position_matin else None, 'position_apres_midi': tour.position_apres_midi.nom if tour.position_apres_midi else None, 'commentaire': tour.commentaire}
        versions_existantes = VersionTourDeService.objects.filter(centre=centre, annee=year, mois=month).count()
        nouveau_numero_index = versions_existantes + 1
        numero_version_str = f"{str(month).zfill(2)}{year}-{nouveau_numero_index}"
        VersionTourDeService.objects.create(centre=centre, annee=year, mois=month, numero_version=numero_version_str, valide_par=request.user, donnees_planning=planning_snapshot)
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

# ==============================================================================
# SECTION VI : GESTION DES FEUILLES DE TEMPS
# ==============================================================================

@login_required
@permission_required('core.view_feuilletemps', raise_exception=True)
def feuille_de_temps_view(request, centre_id, jour=None):
    """ Sert la page squelette pour la Feuille de Temps d'un jour donné (aujourd'hui par défaut). """
    centre = get_object_or_404(Centre, pk=centre_id)
    jour_str = jour or date.today().isoformat()
    date_jour = date.fromisoformat(jour_str)

    jour_precedent = (date_jour - timedelta(days=1)).isoformat()
    jour_suivant = (date_jour + timedelta(days=1)).isoformat()
    peut_aller_au_suivant = date_jour < date.today()

    user_can_edit = request.user.has_perm('core.change_feuilletemps')
    verrou_par = None
    est_cloturee = FeuilleTempsCloture.objects.filter(centre=centre, date_jour=date_jour, reouverte_le__isnull=True).exists()

    if est_cloturee:
        user_can_edit = False
    elif user_can_edit:
        FeuilleTempsVerrou.objects.filter(centre=centre, verrouille_a__lt=timezone.now() - timedelta(hours=1)).delete()
        verrou, created = FeuilleTempsVerrou.objects.get_or_create(
            centre=centre, defaults={'chef_de_quart': request.user.agent_profile}
        )
        if not created and verrou.chef_de_quart != request.user.agent_profile:
            user_can_edit = False
            verrou_par = verrou.chef_de_quart
            
    context = {
        'centre': centre, 'jour_str': jour_str, 'date_jour': date_jour, 'user_can_edit': user_can_edit,
        'verrou_par': verrou_par, 'est_cloturee': est_cloturee,
        'user_can_reouvrir': request.user.has_perm('core.reouvrir_feuilletemps'),
        'jour_precedent_url': reverse('feuille-temps-specific-jour', args=[centre.id, jour_precedent]),
        'jour_suivant_url': reverse('feuille-temps-specific-jour', args=[centre.id, jour_suivant]) if peut_aller_au_suivant else None,
    }
    return render(request, 'core/feuille_de_temps.html', context)

@login_required
@permission_required('core.view_feuilletemps', raise_exception=True)
def api_get_feuille_temps_data(request, centre_id, jour):
    """ API qui renvoie les données du jour, en incluant l'état de clôture. """
    centre = get_object_or_404(Centre, pk=centre_id)
    date_jour = date.fromisoformat(jour)
    est_cloturee = FeuilleTempsCloture.objects.filter(centre=centre, date_jour=date_jour, reouverte_le__isnull=True).exists()
    
    version_tds = VersionTourDeService.objects.filter(
        centre=centre, annee=date_jour.year, mois=date_jour.month
    ).order_by('-date_validation').first()

    if not version_tds:
        return JsonResponse({'error': 'Aucune version validée du TDS trouvée pour ce mois.'}, status=404)

    tds_data = version_tds.donnees_planning
    date_jour_iso = date_jour.isoformat()
    agents_ids_prevus = [int(aid) for aid, p in tds_data.items() if date_jour_iso in p.get('planning', {})]

    planning_du_jour = []
    if agents_ids_prevus:
        agents_obj = {a.id_agent: a for a in Agent.objects.filter(id_agent__in=agents_ids_prevus)}
        pointages_existants = {p.agent_id: p for p in FeuilleTempsEntree.objects.filter(agent_id__in=agents_ids_prevus, date_jour=date_jour)}
        for agent_id in agents_ids_prevus:
            agent = agents_obj.get(agent_id)
            if not agent: continue
            
            planning_data = tds_data.get(str(agent_id), {}).get('planning', {}).get(date_jour_iso, {})
            pointage = pointages_existants.get(agent_id)
            pos_matin_nom = planning_data.get('position_matin')
            
            categorie = "NON_TRAVAIL"
            if pos_matin_nom:
                try:
                    categorie = PositionJour.objects.get(nom=pos_matin_nom, centre=centre).categorie
                except PositionJour.DoesNotExist: pass

            planning_du_jour.append({
                'agent_id': agent.id_agent, 'trigram': agent.trigram,
                'position_matin': pos_matin_nom or 'N/A',
                'position_apres_midi': planning_data.get('position_apres_midi') or 'N/A',
                'commentaire_tds': planning_data.get('commentaire', ''),
                'heure_arrivee': pointage.heure_arrivee.strftime('%H:%M') if pointage and pointage.heure_arrivee else '',
                'heure_depart': pointage.heure_depart.strftime('%H:%M') if pointage and pointage.heure_depart else '',
                'categorie': categorie,
            })
        
    return JsonResponse({
        'planning_du_jour': sorted(planning_du_jour, key=lambda x: x['trigram']),
        'est_cloturee': est_cloturee
    })

@require_POST
@login_required
@permission_required('core.change_feuilletemps', raise_exception=True)
def api_update_feuille_temps(request):
    """ API pour sauvegarder une heure de la Feuille de Temps. """
    data = json.loads(request.body)
    try:
        entree, _ = FeuilleTempsEntree.objects.get_or_create(
            agent_id=data.get('agent_id'), date_jour=date.fromisoformat(data.get('date_jour')),
            defaults={'modifie_par': request.user}
        )
        valeur = data.get('valeur')
        setattr(entree, data.get('champ'), valeur if valeur else None)
        entree.modifie_par = request.user
        entree.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@login_required
@permission_required('core.change_feuilletemps', raise_exception=True)
def api_valider_horaires(request):
    """ API pour la validation en temps réel des règles horaires. """
    data = json.loads(request.body)
    try:
        agent = Agent.objects.get(pk=data['agent_id'])
        date_jour = date.fromisoformat(data['date_jour'])
        heure_arrivee = datetime.strptime(data['heure_arrivee'], '%H:%M').time() if data.get('heure_arrivee') else None
        heure_depart = datetime.strptime(data['heure_depart'], '%H:%M').time() if data.get('heure_depart') else None
        est_j_plus_1 = data.get('est_j_plus_1', False)

        erreurs = verifier_regles_horaires(agent, date_jour, heure_arrivee, heure_depart, est_j_plus_1)
        
        return JsonResponse({'status': 'ok', 'erreurs': erreurs})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@login_required
@permission_required('core.change_feuilletemps', raise_exception=True)
def api_forcer_verrou(request):
    """ API pour forcer la prise de main sur la Feuille de Temps. """
    data = json.loads(request.body)
    centre = get_object_or_404(Centre, pk=data['centre_id'])
    FeuilleTempsVerrou.objects.update_or_create(
        centre=centre, 
        defaults={'chef_de_quart': request.user.agent_profile, 'verrouille_a': timezone.now()}
    )
    return JsonResponse({'status': 'ok'})

@require_POST
@login_required
@permission_required('core.change_feuilletemps', raise_exception=True)
def api_cloturer_journee(request):
    """ API pour clôturer ou re-clôturer une journée de pointage. """
    data = json.loads(request.body)
    centre = get_object_or_404(Centre, pk=data['centre_id'])
    date_jour = date.fromisoformat(data['date_jour'])
    
    # On utilise update_or_create pour gérer tous les cas de figure proprement
    # 1. S'il n'y a aucune entrée pour ce jour, il la crée.
    # 2. S'il y a déjà une entrée (qui a forcément été réouverte), il la met à jour.
    FeuilleTempsCloture.objects.update_or_create(
        centre=centre,
        date_jour=date_jour,
        defaults={
            'cloture_par': request.user,
            'cloture_le': timezone.now(),
            # On s'assure de bien remettre à zéro les champs de réouverture
            'reouverte_par': None,
            'reouverte_le': None,
        }
    )
    
    return JsonResponse({'status': 'ok'})

@require_POST
@login_required
@permission_required('core.reouvrir_feuilletemps', raise_exception=True)
def api_reouvrir_journee(request):
    """ API pour rouvrir une journée (nécessite une permission spéciale). """
    data = json.loads(request.body)
    centre = get_object_or_404(Centre, pk=data['centre_id'])
    date_jour = date.fromisoformat(data['date_jour'])
    
    cloture = get_object_or_404(FeuilleTempsCloture, centre=centre, date_jour=date_jour, reouverte_le__isnull=True)
    cloture.reouverte_par = request.user
    cloture.reouverte_le = timezone.now()
    cloture.save()
    
    return JsonResponse({'status': 'ok'})