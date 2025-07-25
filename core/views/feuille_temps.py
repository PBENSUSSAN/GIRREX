# ==============================================================================
# Fichier : core/views/feuille_temps.py
# Vues et API pour le module "Feuille de Temps".
# ==============================================================================

import json
from datetime import date, timedelta, datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

# On utilise un import relatif pour accéder aux modules de la même application
from ..models import (
    Agent, Centre, FeuilleTempsEntree, FeuilleTempsVerrou, FeuilleTempsCloture,
    PositionJour, VersionTourDeService, ServiceJournalier
)
from ..services import verifier_regles_horaires


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
    FeuilleTempsCloture.objects.update_or_create(
        centre=centre, date_jour=date_jour,
        defaults={
            'cloture_par': request.user, 'cloture_le': timezone.now(),
            'reouverte_par': None, 'reouverte_le': None,
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

@login_required
@permission_required('core.open_close_service', raise_exception=True)
def gerer_service_view(request, centre_id):
    """
    Gère l'ouverture et la clôture du service journalier via une page de confirmation.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    today = date.today()
    service = ServiceJournalier.objects.filter(centre=centre, date_jour=today).first()
    
    action = 'ouvrir' if not service else 'cloturer'
    
    if request.method == 'POST':
        # --- CAS 1: On ouvre le service ---
        if action == 'ouvrir':
            ServiceJournalier.objects.create(
                centre=centre,
                date_jour=today,
                cdq_ouverture=request.user.agent_profile,
                heure_ouverture=timezone.now().time(),
                ouvert_par=request.user,
                statut=ServiceJournalier.StatutJournee.OUVERTE
            )
            messages.success(request, f"Le service pour le {today.strftime('%d/%m/%Y')} a été ouvert avec succès.")
        
        # --- CAS 2: On clôture le service ---
        elif service.statut == ServiceJournalier.StatutJournee.OUVERTE:
            service.cdq_cloture = request.user.agent_profile
            service.heure_cloture = timezone.now().time()
            service.cloture_par = request.user
            service.statut = ServiceJournalier.StatutJournee.CLOTUREE
            service.save()
            messages.success(request, f"Le service pour le {today.strftime('%d/%m/%Y')} a été clôturé avec succès.")
            
        else:
            messages.warning(request, "L'action demandée n'est pas valide (le service est peut-être déjà clôturé).")

        # On redirige vers le cahier de marche du jour pour voir le résultat
        return redirect('cahier-de-marche', centre_id=centre.id, jour=today.strftime('%Y-%m-%d'))

    # Si la méthode est GET, on affiche la page de confirmation
    context = {
        'centre': centre,
        'service': service,
        'action': action
    }
    return render(request, 'core/gerer_service.html', context)