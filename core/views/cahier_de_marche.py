# Fichier : core/views/cahier_de_marche.py (VERSION REFACTORISÉE POUR AFFICHAGE CATÉGORISÉ)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, time, timedelta
from ..models import Centre, FeuilleTempsEntree, PanneCentre, EvenementCentre
from ..forms import PanneCentreForm, EvenementCentreForm
from ..decorators import effective_permission_required, cdq_lock_required

@effective_permission_required('core.view_feuilletemps')
def cahier_de_marche_view(request, centre_id, jour):
    """
    Prépare les données pour le Cahier de Marche en les groupant par catégorie :
    - Pannes actives durant la journée.
    - Événements survenus durant la journée.
    - Mouvements du personnel (pointages) de la journée.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    try:
        target_date = datetime.strptime(jour, "%Y-%m-%d").date()
    except ValueError:
        target_date = timezone.now().date()
    
    # Création de trois listes distinctes
    pannes_du_jour = []
    evenements_du_jour = []
    mouvements_du_jour = []

    start_of_day = timezone.make_aware(datetime.combine(target_date, time.min))
    end_of_day = timezone.make_aware(datetime.combine(target_date, time.max))

    # --- Catégorie 1 : Pannes ---
    pannes_query = PanneCentre.objects.filter(
        centre=centre, date_heure_debut__lte=end_of_day
    ).filter(
        Q(date_heure_fin__gte=start_of_day) | Q(date_heure_fin__isnull=True)
    ).order_by('date_heure_debut')
    pannes_du_jour = list(pannes_query) # On transforme le queryset en liste

    # --- Catégorie 2 : Événements ---
    evenements_query = EvenementCentre.objects.filter(
        centre=centre, 
        date_heure_evenement__gte=start_of_day, 
        date_heure_evenement__lte=end_of_day
    ).order_by('date_heure_evenement')
    evenements_du_jour = list(evenements_query)

    # --- Catégorie 3 : Mouvements du personnel ---
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
    
    # On trie les mouvements par ordre chronologique
    mouvements_du_jour.sort(key=lambda item: item['timestamp'])

    # Le contexte contient maintenant nos trois listes séparées
    context = { 
        'centre': centre, 
        'jour_selectionne': target_date, 
        'pannes': pannes_du_jour,
        'evenements': evenements_du_jour,
        'mouvements': mouvements_du_jour,
    }
    return render(request, 'core/cahier_de_marche.html', context)


# ... (les vues de formulaire ajouter_panne_view et ajouter_evenement_view ne changent pas) ...
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