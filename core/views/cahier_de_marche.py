# Fichier : core/views/cahier_de_marche.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.urls import reverse

from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Import des modèles
from ..models import Centre, FeuilleTempsEntree, EvenementCentre, ServiceJournalier, ServiceJournalierHistorique, ActiviteZone
from technique.models import PanneCentre, Miso, PanneHistorique # Miso et PanneHistorique sont importés

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
    
    ⚠️ SÉCURITÉ : Vérifie que l'utilisateur a le droit de voir CE centre.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    
    # ✅ CONTRÔLE DE SÉCURITÉ
    if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Vous devez être un agent pour accéder au cahier de marche.")
    
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
            f"Vous n'avez pas l'autorisation d'accéder au cahier de marche du centre {centre.code_centre}."
        )
    
    try:
        target_date = datetime.strptime(jour, "%Y-%m-%d").date()
    except ValueError:
        target_date = timezone.now().date()
    
    start_of_day = timezone.make_aware(datetime.combine(target_date, time.min))
    end_of_day = timezone.make_aware(datetime.combine(target_date, time.max))
    
    historique_service = ServiceJournalierHistorique.objects.filter(
        service_journalier__centre=centre, 
        service_journalier__date_jour=target_date
    ).select_related('agent_action').order_by('timestamp')

    pannes_du_jour = list(PanneCentre.objects.filter(
        centre=centre, date_heure_debut__lte=end_of_day
    ).filter(
        Q(date_heure_fin__gte=start_of_day) | Q(date_heure_fin__isnull=True)
    ).order_by('date_heure_debut'))

    evenements_du_jour = list(EvenementCentre.objects.filter(
        centre=centre, 
        date_heure_evenement__gte=start_of_day, 
        date_heure_evenement__lte=end_of_day
    ).order_by('date_heure_evenement'))

    activites_zone_du_jour = list(ActiviteZone.objects.filter(
        zone__centre=centre,
        timestamp__gte=start_of_day,
        timestamp__lte=end_of_day
    ).select_related('zone', 'agent_action').order_by('timestamp'))

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

    miso_du_jour = list(Miso.objects.filter(
        centre=centre,
        statut_override__isnull=True,
        date_debut__lte=end_of_day,
        date_fin__gte=start_of_day
    ).order_by('date_debut'))

    context = { 
        'centre': centre, 
        'jour_selectionne': target_date, 
        'pannes': pannes_du_jour,
        'evenements': evenements_du_jour,
        'mouvements': mouvements_du_jour,
        'historique_service': historique_service,
        'activites_zone': activites_zone_du_jour,
        'miso_du_jour': miso_du_jour,
    }
    return render(request, 'core/cahier_de_marche.html', context)


@cdq_lock_required
@effective_permission_required('technique.add_pannecentre', raise_exception=True)
def ajouter_panne_view(request, centre_id):
    """
    Gère la création d'une panne et redirige intelligemment.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    
    # On détermine l'URL de redirection. Par défaut, le cahier de marche.
    default_redirect = reverse('cahier-de-marche', args=[centre.id, timezone.now().strftime('%Y-%m-%d')])
    next_url = request.GET.get('next', default_redirect)

    if request.method == 'POST':
        form = PanneCentreForm(request.POST)
        if form.is_valid():
            panne = form.save(commit=False)
            panne.centre = centre
            panne.auteur = request.user.agent_profile
            panne.save()

            # Création de l'entrée d'historique pour la traçabilité
            PanneHistorique.objects.create(
                panne=panne,
                type_evenement=PanneHistorique.TypeEvenement.CREATION,
                auteur=request.user,
                details={'message': 'Création initiale de la panne.'}
            )

            messages.success(request, "La panne a été enregistrée avec succès.")
            return redirect(next_url) # Redirection dynamique
    else:
        form = PanneCentreForm(initial={'date_heure_debut': timezone.now()})
    
    context = {
        'form': form, 
        'titre': 'Signaler une nouvelle panne', 
        'centre': centre,
        'form_action_url': request.get_full_path() # Passe l'URL complète au template
    }
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
@effective_permission_required('technique.resolve_pannecentre', raise_exception=True)
def resoudre_panne_view(request, centre_id, panne_id):
    panne = get_object_or_404(PanneCentre, pk=panne_id, centre_id=centre_id)
    panne.statut = PanneCentre.Statut.RESOLUE
    panne.date_heure_fin = timezone.now()
    panne.save()

    # Création de l'entrée d'historique pour la traçabilité de la résolution rapide
    PanneHistorique.objects.create(
        panne=panne,
        type_evenement=PanneHistorique.TypeEvenement.RESOLUTION,
        auteur=request.user,
        details={'message': 'Résolution rapide depuis le Cahier de Marche.'}
    )

    return JsonResponse({'status': 'ok', 'message': 'La panne a été marquée comme résolue.'})