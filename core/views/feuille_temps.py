# Fichier : core/views/feuille_temps.py (VERSION CORRIGÉE ET COMPLÈTE)

import json
from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import (
    Agent, Centre, FeuilleTempsEntree, FeuilleTempsVerrou, ServiceJournalier,
    PositionJour, VersionTourDeService, ServiceJournalierHistorique
)
from ..services import verifier_regles_horaires

@login_required
@permission_required('core.view_feuilletemps', raise_exception=True)
def feuille_de_temps_view(request, centre_id, jour=None):
    """
    Vue de la feuille de temps.
    
    ⚠️ SÉCURITÉ : Vérifie que l'utilisateur a le droit de voir CE centre.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    
    # ✅ CONTRÔLE DE SÉCURITÉ
    if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Vous devez être un agent pour accéder à la feuille de temps.")
    
    from core.models import Role
    from django.core.exceptions import PermissionDenied
    
    acces_autorise = False
    
    # 1. Vision NATIONALE
    if request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_FORM
    ]:
        acces_autorise = True
    elif 'competences.view_all_licences' in request.effective_perms:
        acces_autorise = True
    # 2. Accès à SON centre uniquement
    elif request.centre_agent and request.centre_agent.id == centre.id:
        acces_autorise = True
    
    if not acces_autorise:
        raise PermissionDenied(
            f"Vous n'avez pas l'autorisation d'accéder à la feuille de temps du centre {centre.code_centre}."
        )
    
    jour_str = jour or date.today().isoformat()
    date_jour = date.fromisoformat(jour_str)
    jour_precedent = (date_jour - timedelta(days=1)).isoformat()
    jour_suivant = (date_jour + timedelta(days=1)).isoformat()
    peut_aller_au_suivant = date_jour < date.today()
    service_journalier = ServiceJournalier.objects.filter(centre=centre, date_jour=date_jour).first()
    verrou = FeuilleTempsVerrou.objects.filter(centre=centre).first()
    est_cloturee = service_journalier and service_journalier.statut in [ServiceJournalier.StatutJournee.CLOTUREE, ServiceJournalier.StatutJournee.VISEE]
    verrou_par = verrou.chef_de_quart if verrou else None
    user_can_edit = not est_cloturee and request.user.has_perm('core.change_feuilletemps')
    context = {
        'centre': centre, 'jour_str': jour_str, 'date_jour': date_jour, 'user_can_edit': user_can_edit,
        'verrou_par': verrou_par, 'est_cloturee': est_cloturee,
        'jour_precedent_url': reverse('feuille-temps-specific-jour', args=[centre.id, jour_precedent]),
        'jour_suivant_url': reverse('feuille-temps-specific-jour', args=[centre.id, jour_suivant]) if peut_aller_au_suivant else None,
    }
    return render(request, 'core/feuille_de_temps.html', context)

@login_required
@require_POST
def gerer_service_view(request, centre_id, action):
    centre = get_object_or_404(Centre, pk=centre_id)
    today = date.today()
    
    # On utilise la même logique que le context_processor pour trouver sur quel service agir.
    service_a_modifier = ServiceJournalier.objects.filter(
        centre=centre, statut=ServiceJournalier.StatutJournee.OUVERTE
    ).order_by('-date_jour').first()

    # Si on ouvre, le service n'existe pas encore.
    if action == 'ouvrir':
        service_a_modifier = None

    if not hasattr(request.user, 'agent_profile'):
        messages.error(request, "Action impossible : votre compte utilisateur n'est pas lié à un profil Agent.")
        return redirect(reverse('home'))

    try:
        with transaction.atomic():
            agent_qui_agit = request.user.agent_profile
            
            if action == 'ouvrir' and not service_a_modifier and request.user.has_perm('core.open_close_service'):
                nouveau_service = ServiceJournalier.objects.create(centre=centre, date_jour=today, cdq_ouverture=agent_qui_agit, heure_ouverture=timezone.now().time(), ouvert_par=request.user, statut=ServiceJournalier.StatutJournee.OUVERTE)
                FeuilleTempsVerrou.objects.update_or_create(centre=centre, defaults={'chef_de_quart': agent_qui_agit})
                ServiceJournalierHistorique.objects.create(service_journalier=nouveau_service, type_action=ServiceJournalierHistorique.ActionType.OUVERTURE, modifie_par=request.user, agent_action=agent_qui_agit)
                messages.success(request, f"Le service du {today.strftime('%d/%m/%Y')} a été ouvert. Vous avez le contrôle.")

            elif action == 'cloturer' and service_a_modifier and service_a_modifier.statut == 'OUVERTE' and request.user.has_perm('core.open_close_service'):
                service_a_modifier.cdq_cloture = agent_qui_agit
                service_a_modifier.heure_cloture = timezone.now().time()
                service_a_modifier.cloture_par = request.user
                service_a_modifier.statut = ServiceJournalier.StatutJournee.CLOTUREE
                service_a_modifier.save()
                FeuilleTempsVerrou.objects.filter(centre=centre).delete()
                ServiceJournalierHistorique.objects.create(service_journalier=service_a_modifier, type_action=ServiceJournalierHistorique.ActionType.CLOTURE, modifie_par=request.user, agent_action=agent_qui_agit)
                messages.success(request, f"Le service du {service_a_modifier.date_jour.strftime('%d/%m/%Y')} a été clôturé.")

            elif action == 'reouvrir' and request.user.has_perm('core.reopen_service'):
                 service_a_reouvrir = ServiceJournalier.objects.filter(centre=centre, date_jour=today, statut=ServiceJournalier.StatutJournee.CLOTUREE).first()
                 if service_a_reouvrir:
                    service_a_reouvrir.statut = ServiceJournalier.StatutJournee.OUVERTE
                    service_a_reouvrir.cdq_cloture, service_a_reouvrir.heure_cloture, service_a_reouvrir.cloture_par = None, None, None
                    service_a_reouvrir.save()
                    FeuilleTempsVerrou.objects.update_or_create(centre=centre, defaults={'chef_de_quart': agent_qui_agit})
                    ServiceJournalierHistorique.objects.create(service_journalier=service_a_reouvrir, type_action=ServiceJournalierHistorique.ActionType.REOUVERTURE, modifie_par=request.user, agent_action=agent_qui_agit)
                    messages.success(request, f"Le service du {today.strftime('%d/%m/%Y')} a été ROUVERT. Vous avez le contrôle.")
                 else:
                    messages.error(request, "Aucun service clôturé aujourd'hui n'a été trouvé pour être rouvert.")
            
            # ==============================================================================
            # BLOC CORRIGÉ / AJOUTÉ : GESTION DU FORÇAGE DE PRISE DE MAIN
            # ==============================================================================
            elif action == 'forcer-prise' and service_a_modifier and request.user.has_perm('core.change_feuilletemps'):
                verrou = FeuilleTempsVerrou.objects.filter(centre=centre).first()
                if verrou:
                    ancien_cdq = verrou.chef_de_quart
                    verrou.chef_de_quart = agent_qui_agit
                    verrou.verrouille_a = timezone.now()
                    verrou.save()
                    messages.warning(request, f"Vous avez forcé la prise de contrôle qui était détenue par {ancien_cdq}. Vous avez maintenant la main.")
                else:
                    # Sécurité : si le service est ouvert mais qu'aucun verrou n'existe (cas anormal), on le crée.
                    FeuilleTempsVerrou.objects.update_or_create(centre=centre, defaults={'chef_de_quart': agent_qui_agit})
                    messages.success(request, "Vous avez pris le contrôle du service.")
            # ==============================================================================
            
            else:
                messages.error(request, "Action non autorisée ou non valide.")
    except Exception as e:
        messages.error(request, f"Une erreur technique est survenue : {e}")

    return redirect('cahier-de-marche', centre_id=centre.id, jour=today.strftime('%Y-%m-%d'))

@login_required
@permission_required('core.view_feuilletemps', raise_exception=True)
def api_get_feuille_temps_data(request, centre_id, jour):
    centre = get_object_or_404(Centre, pk=centre_id)
    date_jour = date.fromisoformat(jour)
    service = ServiceJournalier.objects.filter(centre=centre, date_jour=date_jour).first()
    est_cloturee = service and service.statut != ServiceJournalier.StatutJournee.OUVERTE
    version_tds = VersionTourDeService.objects.filter(centre=centre, annee=date_jour.year, mois=date_jour.month).order_by('-date_validation').first()
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
            categorie = "NON-TRAVAIL"
            if pos_matin_nom:
                try: categorie = PositionJour.objects.get(nom=pos_matin_nom, centre=centre).categorie
                except PositionJour.DoesNotExist: pass
            planning_du_jour.append({'agent_id': agent.id_agent, 'trigram': agent.trigram, 'position_matin': pos_matin_nom or 'N/A', 'position_apres_midi': planning_data.get('position_apres_midi') or 'N/A', 'commentaire_tds': planning_data.get('commentaire', ''), 'heure_arrivee': pointage.heure_arrivee.strftime('%H:%M') if pointage and pointage.heure_arrivee else '', 'heure_depart': pointage.heure_depart.strftime('%H:%M') if pointage and pointage.heure_depart else '', 'categorie': categorie,})
    return JsonResponse({'planning_du_jour': sorted(planning_du_jour, key=lambda x: x['trigram']), 'est_cloturee': est_cloturee})

@require_POST
@login_required
@permission_required('core.change_feuilletemps', raise_exception=True)
def api_update_feuille_temps(request):
    data = json.loads(request.body)
    try:
        entree, _ = FeuilleTempsEntree.objects.get_or_create(agent_id=data.get('agent_id'), date_jour=date.fromisoformat(data.get('date_jour')), defaults={'modifie_par': request.user})
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
    data = json.loads(request.body)
    centre = get_object_or_404(Centre, pk=data['centre_id'])
    FeuilleTempsVerrou.objects.update_or_create(centre=centre, defaults={'chef_de_quart': request.user.agent_profile, 'verrouille_a': timezone.now()})
    return JsonResponse({'status': 'ok'})