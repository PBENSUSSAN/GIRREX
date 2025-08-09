# Fichier : core/views/cahier_de_marche.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, time, timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Import des modèles
from ..models import Centre, FeuilleTempsEntree, EvenementCentre, ServiceJournalier, ServiceJournalierHistorique, ActiviteZone
from technique.models import PanneCentre, Miso  # Miso est maintenant importé ici

# Import des formulaires
from ..forms import EvenementCentreForm
from technique.forms import PanneCentreForm

# Import des décorateurs
from ..decorators import effective_permission_required, cdq_lock_required

@effective_permission_required('core.view_feuilletemps')
def cahier_de_marche_view(request, centre_id, jour):
    """
    Prépare les données pour le Cahier de Marche, en incluant l'historique du service
    et les préavis de maintenance (MISO).
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    try:
        target_date = datetime.strptime(jour, "%Y-%m-%d").date()
    except ValueError:
        target_date = timezone.now().date()
    
    # Définition de la plage horaire pour la journée consultée
    start_of_day = timezone.make_aware(datetime.combine(target_date, time.min))
    end_of_day = timezone.make_aware(datetime.combine(target_date, time.max))
    
    # --- Récupération des données par catégorie ---

    # 1. Historique du service
    historique_service = ServiceJournalierHistorique.objects.filter(
        service_journalier__centre=centre, 
        service_journalier__date_jour=target_date
    ).select_related('agent_action').order_by('timestamp')

    # 2. Pannes actives sur la journée
    pannes_du_jour = list(PanneCentre.objects.filter(
        centre=centre, date_heure_debut__lte=end_of_day
    ).filter(
        Q(date_heure_fin__gte=start_of_day) | Q(date_heure_fin__isnull=True)
    ).order_by('date_heure_debut'))

    # 3. Événements consignés dans la journée
    evenements_du_jour = list(EvenementCentre.objects.filter(
        centre=centre, 
        date_heure_evenement__gte=start_of_day, 
        date_heure_evenement__lte=end_of_day
    ).order_by('date_heure_evenement'))

    # 4. Activités des zones dans la journée
    activites_zone_du_jour = list(ActiviteZone.objects.filter(
        zone__centre=centre,
        timestamp__gte=start_of_day,
        timestamp__lte=end_of_day
    ).select_related('zone', 'agent_action').order_by('timestamp'))

    # 5. Mouvements du personnel (entrées/sorties)
    mouvements_du_jour = []
    pointages = FeuilleTempsEntree.objects.filter(agent__centre=centre, date_jour=target_date)
    for p in pointages:
        if p.heure_arrivee:
            naive_dt = datetime.combine(target_date, p.heure_arrivee)
            mouvements_du_jour.append({'type': 'arrivee', 'agent': p.agent, 'timestamp': timezone.make_aware(naive_dt)})
        if p.heure_depart:
            depart_date = target_date
            if p.heure_arrivee and p.heure_depart < p.heure_arrivee:
                depart_date += timedelta(days=1)
            naive_dt = datetime.combine(depart_date, p.heure_depart)
            mouvements_du_jour.append({'type': 'depart', 'agent': p.agent, 'timestamp': timezone.make_aware(naive_dt)})
    mouvements_du_jour.sort(key=lambda item: item['timestamp'])

    # 6. NOUVEAU : Récupération des MISO pertinents pour le jour
    miso_du_jour = list(Miso.objects.filter(
        centre=centre,
        statut_override__isnull=True,   # On exclut les MISO qui ont été annulés
        date_debut__lte=end_of_day,     # Le MISO doit commencer avant la fin de la journée
        date_fin__gte=start_of_day      # Et se terminer après le début de la journée
    ).order_by('date_debut'))

    # --- Préparation du contexte pour le template ---
    context = { 
        'centre': centre, 
        'jour_selectionne': target_date, 
        'pannes': pannes_du_jour,
        'evenements': evenements_du_jour,
        'mouvements': mouvements_du_jour,
        'historique_service': historique_service,
        'activites_zone': activites_zone_du_jour,
        'miso_du_jour': miso_du_jour,  # On ajoute les MISO au contexte
    }
    return render(request, 'core/cahier_de_marche.html', context)


#
# Les vues ci-dessous (ajouter_panne, ajouter_evenement, resoudre_panne)
# restent inchangées car leur logique est déjà correcte et découplée.
#

@cdq_lock_required
@effective_permission_required('core.add_pannecentre')
def ajouter_panne_view(request, centre_id):
    centre = get_object_or_404(Centre, pk=centre_id)
    if request.method == 'POST':
        form = PanneCentreForm(request.POST)
        if form.is_valid():
            panne = form.save(commit=False)
            panne.centre = centre
            panne.auteur = request.user.agent_profile
            panne.save()
            messages.success(request, "La panne a été enregistrée avec succès.")
            return redirect('cahier-de-marche', centre_id=centre.id, jour=timezone.now().strftime('%Y-%m-%d'))
    else:
        form = PanneCentreForm(initial={'date_heure_debut': timezone.now()})
    context = {'form': form, 'titre': 'Signaler une nouvelle panne', 'centre': centre}
    return render(request, 'core/form_generique.html', context)


@cdq_lock_required
@effective_permission_required('core.add_evenementcentre')
def ajouter_evenement_view(request, centre_id):
    centre = get_object_or_404(Centre, pk=centre_id)
    if request.method == 'POST':
        form = EvenementCentreForm(request.POST, centre=centre)
        if form.is_valid():
            evenement = form.save(commit=False)
            evenement.centre = centre
            evenement.auteur = request.user.agent_profile
            evenement.save()
            messages.success(request, "L'événement a été consigné avec succès.")
            return redirect('cahier-de-marche', centre_id=centre.id, jour=timezone.now().strftime('%Y-%m-%d'))
    else:
        form = EvenementCentreForm(centre=centre, initial={'date_heure_evenement': timezone.now()})
    context = {'form': form, 'titre': 'Consigner un nouvel événement', 'centre': centre}
    return render(request, 'core/form_generique.html', context)


@require_POST
@cdq_lock_required
@effective_permission_required('core.resolve_pannecentre', raise_exception=True)
def resoudre_panne_view(request, centre_id, panne_id):
    panne = get_object_or_404(PanneCentre, pk=panne_id, centre_id=centre_id)
    panne.statut = PanneCentre.Statut.RESOLUE
    panne.date_heure_fin = timezone.now()
    panne.save()
    return JsonResponse({'status': 'ok', 'message': 'La panne a été marquée comme résolue.'})