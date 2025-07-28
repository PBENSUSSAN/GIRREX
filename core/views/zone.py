# Fichier : core/views/zone.py

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from datetime import datetime, time

# On importe les modèles et les décorateurs nécessaires
from ..models import Centre, Zone, ActiviteZone, ServiceJournalier
from ..decorators import effective_permission_required, cdq_lock_required


@effective_permission_required('core.view_zone')
@cdq_lock_required
def gestion_zone_view(request, centre_id):
    """
    Affiche un tableau de bord complet pour la gestion et le suivi des zones.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, time.min))
    end_of_day = timezone.make_aware(datetime.combine(today, time.max))

    # --- 1. LISTE DES ZONES POUR LE PILOTAGE (Colonne de gauche) ---
    zones_du_centre = Zone.objects.filter(centre=centre).order_by('nom')

    # --- 2. HISTORIQUE DES ACTIVITÉS DU JOUR (Carte en haut à droite) ---
    historique_du_jour = ActiviteZone.objects.filter(
        zone__centre=centre,
        timestamp__gte=start_of_day,
        timestamp__lte=end_of_day
    ).select_related('zone', 'agent_action').order_by('timestamp')

    # --- 3. CALCUL DES STATISTIQUES (Carte en bas à droite) ---
    stats_zones = []
    # On parcourt chaque zone du centre pour calculer ses statistiques
    for zone in zones_du_centre:
        # On récupère toutes les activités de la journée pour cette zone spécifique
        activites_zone_jour = historique_du_jour.filter(zone=zone)
        
        nombre_activations = 0
        duree_totale = timezone.timedelta(0)
        
        # On cherche la première activation de la journée pour cette zone
        premiere_activation = activites_zone_jour.filter(type_action=ActiviteZone.TypeAction.ACTIVATION).first()
        
        if premiere_activation:
            # On parcourt les paires activation/désactivation
            last_activation_time = None
            for activite in activites_zone_jour:
                if activite.type_action == ActiviteZone.TypeAction.ACTIVATION:
                    nombre_activations += 1
                    # On stocke l'heure de cette activation en attendant une désactivation
                    last_activation_time = activite.timestamp
                
                elif activite.type_action == ActiviteZone.TypeAction.DESACTIVATION and last_activation_time:
                    # On a trouvé une désactivation qui suit une activation : c'est un cycle complet
                    duree_cycle = activite.timestamp - last_activation_time
                    duree_totale += duree_cycle
                    # On réinitialise l'heure de la dernière activation pour éviter de la compter deux fois
                    last_activation_time = None
        
        # On formate la durée totale en H:M:S pour l'affichage
        total_seconds = int(duree_totale.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        duree_formatee = f"{hours:02}:{minutes:02}:{seconds:02}"

        stats_zones.append({
            'nom': zone.nom,
            'nombre_activations': nombre_activations,
            'duree_totale_formatee': duree_formatee,
        })

    context = {
        'centre': centre,
        'titre': 'Gestion des Zones',
        'zones_pilotage': zones_du_centre,       # Données pour la colonne de gauche
        'historique_jour': historique_du_jour,   # Données pour la carte en haut à droite
        'stats_zones': stats_zones,              # Données pour la carte en bas à droite
    }
    return render(request, 'core/gestion_zone.html', context)


@require_POST
@effective_permission_required('core.change_zone')
@cdq_lock_required
def activer_desactiver_zone_view(request, centre_id, zone_id, action):
    """
    Gère la logique d'activation ou de désactivation d'une zone. (INCHANGÉ)
    """
    zone = get_object_or_404(Zone, pk=zone_id, centre_id=centre_id)
    
    service_ouvert = ServiceJournalier.objects.filter(
        centre_id=centre_id, 
        statut=ServiceJournalier.StatutJournee.OUVERTE
    ).first()

    if not service_ouvert:
        messages.error(request, "Action impossible : aucun service n'est actuellement ouvert.")
        return redirect('gestion-zone', centre_id=centre_id)

    try:
        with transaction.atomic():
            agent_qui_agit = request.user.agent_profile
            now = timezone.now()

            if action == 'activer':
                zone.est_active = True
                type_action_historique = ActiviteZone.TypeAction.ACTIVATION
                message_succes = f"La zone '{zone.nom}' a été activée."
            elif action == 'desactiver':
                zone.est_active = False
                type_action_historique = ActiviteZone.TypeAction.DESACTIVATION
                message_succes = f"La zone '{zone.nom}' a été désactivée."
            else:
                messages.error(request, "Action non reconnue.")
                return redirect('gestion-zone', centre_id=centre_id)

            zone.derniere_activite = now
            zone.dernier_agent = agent_qui_agit
            zone.save()

            ActiviteZone.objects.create(
                zone=zone,
                type_action=type_action_historique,
                timestamp=now,
                agent_action=agent_qui_agit,
                service_journalier=service_ouvert
            )
            
            messages.success(request, message_succes)

    except Exception as e:
        messages.error(request, f"Une erreur technique est survenue : {e}")

    return redirect('gestion-zone', centre_id=centre_id)

# ==============================================================================
# MODIFICATION 2 : NOUVELLES VUES API POUR LA MODALE D'ÉDITION
# ==============================================================================

@effective_permission_required('core.view_zone')
def api_get_zones(request, centre_id):
    """ API pour lister les zones d'un centre. Renvoie du JSON. """
    zones = Zone.objects.filter(centre_id=centre_id).values('id', 'nom', 'description').order_by('nom')
    return JsonResponse(list(zones), safe=False)

@require_POST
@effective_permission_required('core.add_zone')
def api_add_zone(request, centre_id):
    """ API pour ajouter une nouvelle zone. """
    try:
        data = json.loads(request.body)
        nom = data.get('nom')
        description = data.get('description', '')
        if not nom:
            return JsonResponse({'status': 'error', 'message': 'Le nom est requis.'}, status=400)
        
        zone, created = Zone.objects.get_or_create(
            centre_id=centre_id, 
            nom=nom,
            defaults={'description': description}
        )
        if not created:
             return JsonResponse({'status': 'error', 'message': f"La zone '{nom}' existe déjà pour ce centre."}, status=400)

        return JsonResponse({'status': 'ok', 'message': f"La zone '{zone.nom}' a été ajoutée."})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@effective_permission_required('core.change_zone')
def api_update_zone(request, zone_id):
    """ API pour modifier une zone existante. """
    try:
        data = json.loads(request.body)
        nom = data.get('nom')
        description = data.get('description', '')
        if not nom:
            return JsonResponse({'status': 'error', 'message': 'Le nom est requis.'}, status=400)

        zone = get_object_or_404(Zone, pk=zone_id)
        zone.nom = nom
        zone.description = description
        zone.save()
        return JsonResponse({'status': 'ok', 'message': f"La zone '{zone.nom}' a été mise à jour."})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@effective_permission_required('core.delete_zone')
def api_delete_zone(request, zone_id):
    """ API pour supprimer une zone. """
    try:
        zone = get_object_or_404(Zone, pk=zone_id)
        nom_zone = zone.nom
        zone.delete()
        return JsonResponse({'status': 'ok', 'message': f"La zone '{nom_zone}' a été supprimée."})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)