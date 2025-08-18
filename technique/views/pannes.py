# Fichier : technique/views/pannes.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import effective_permission_required
from ..models import  PanneCentre, PanneHistorique
from ..forms import PanneCentreForm
from django.utils import timezone
from ..filters import PanneFilter
from django.contrib import messages

@login_required
@effective_permission_required('technique.view_pannecentre', raise_exception=True)
def liste_pannes_view(request):
    """
    Affiche la bibliothèque des pannes, en respectant le contexte de l'utilisateur.
    """
    base_queryset = PanneCentre.objects.select_related('centre', 'auteur')

    # On applique le filtre contextuel : un local ne voit que son centre
    if hasattr(request, 'centre_agent') and request.centre_agent:
        base_queryset = base_queryset.filter(centre=request.centre_agent)

    panne_filter = PanneFilter(request.GET, queryset=base_queryset)
    context = {
        'filter': panne_filter,
        'titre': "Bibliothèque des Pannes",
        'today': timezone.now().date(),
    }
    return render(request, 'technique/liste_pannes.html', context)


@login_required
@effective_permission_required('technique.view_pannecentre', raise_exception=True)
def detail_panne_view(request, panne_id):
    """
    Affiche le détail d'une panne et gère sa modification.
    """
    panne_instance = get_object_or_404(PanneCentre, pk=panne_id)
    historique = panne_instance.historique.all().order_by('-timestamp')
    can_edit = request.user.has_perm('technique.change_pannecentre')

    if request.method == 'POST' and can_edit:
        form = PanneCentreForm(request.POST, instance=panne_instance)
        if form.is_valid():
            form.save()
            
            # On récupère le commentaire du formulaire
            commentaire = form.cleaned_data.get('commentaire_mise_a_jour')

            PanneHistorique.objects.create(
                panne=panne_instance,
                type_evenement=PanneHistorique.TypeEvenement.MODIFICATION,
                auteur=request.user,
                # On sauvegarde le commentaire dans les détails de l'historique
                details={'message': commentaire or 'Modification des détails de la panne.'}
            )
            messages.success(request, "La panne a été mise à jour.")
            return redirect('technique:detail-panne', panne_id=panne_instance.id)
    else:
        form = PanneCentreForm(instance=panne_instance)

    if not can_edit:
        for field in form.fields.values():
            field.disabled = True

    context = {
        'form': form,
        'panne': panne_instance,
        'historique': historique,
        'can_edit': can_edit,
        'titre': f"Détail de la Panne #{panne_instance.id}"
    }
    return render(request, 'technique/detail_panne.html', context)
    
@login_required
@effective_permission_required('technique.resolve_pannecentre', raise_exception=True)
def resoudre_panne_view(request, panne_id):
    """
    Marque une panne comme résolue.
    """
    panne = get_object_or_404(PanneCentre, pk=panne_id)
    
    if panne.statut == PanneCentre.Statut.EN_COURS:
        panne.statut = PanneCentre.Statut.RESOLUE
        panne.date_heure_fin = timezone.now()
        panne.save()

        PanneHistorique.objects.create(
            panne=panne,
            type_evenement=PanneHistorique.TypeEvenement.RESOLUTION,
            auteur=request.user,
            details={'message': f"Panne marquée comme résolue par {request.user.username}."}
        )
        messages.success(request, "La panne a été marquée comme résolue.")
    else:
        messages.warning(request, "Cette panne est déjà résolue.")

    return redirect('technique:liste-pannes')

@login_required
@effective_permission_required('technique.add_pannecentre', raise_exception=True)
def creer_panne_administrative_view(request):
    """
    Vue DÉDIÉE à la création d'une panne par un utilisateur habilité
    (ex: ES Local) DEPUIS LA BIBLIOTHÈQUE.
    Cette vue ne vérifie PAS le verrou du CDQ.
    """
    if not hasattr(request.user, 'agent_profile'):
        messages.error(request, "Votre compte n'est pas lié à un profil Agent.")
        return redirect('technique:liste-pannes')
        
    centre_utilisateur = getattr(request, 'centre_agent', None)
    if not centre_utilisateur:
        messages.error(request, "Impossible de déterminer votre centre de travail. Veuillez sélectionner un rôle local.")
        return redirect('technique:liste-pannes')

    if request.method == 'POST':
        # Le formulaire n'inclut pas le champ 'centre', on le passe en initial
        form = PanneCentreForm(request.POST, initial={'centre': centre_utilisateur})
        if form.is_valid():
            panne = form.save(commit=False)
            panne.centre = centre_utilisateur # Assignation explicite du centre depuis le contexte
            panne.auteur = request.user.agent_profile
            panne.save()

            PanneHistorique.objects.create(
                panne=panne,
                type_evenement=PanneHistorique.TypeEvenement.CREATION,
                auteur=request.user,
                details={'message': f'Création (administrative) par {request.user.username} depuis la bibliothèque.'}
            )
            messages.success(request, f"La panne pour le centre {panne.centre.code_centre} a été enregistrée.")
            return redirect('technique:liste-pannes')
    else:
        form = PanneCentreForm()
    
    # On s'assure que le formulaire n'affiche pas le champ 'centre'
    if 'centre' in form.fields:
        form.fields.pop('centre')
    
    context = {
        'form': form,
        'titre': f"Signaler une panne pour le centre {centre_utilisateur.code_centre}",
        'centre': centre_utilisateur,
    }
    return render(request, 'core/form_generique.html', context)