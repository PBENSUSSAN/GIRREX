# Fichier : technique/views/miso.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Miso, MisoHistorique
from ..forms import MisoForm, AnnulerMisoForm
from suivi.models import HistoriqueAction # Note: Cet import n'est plus utilisé ici, mais on peut le laisser
from ..filters import MisoFilter

# --- AJOUTEZ CETTE LIGNE D'IMPORT ---
from core.decorators import effective_permission_required


@login_required
@effective_permission_required('technique.view_miso', raise_exception=True)
def liste_miso_view(request):
    """
    Affiche la liste des MISO en appliquant les filtres
    et en tenant compte du contexte de l'utilisateur.
    """
    base_queryset = Miso.objects.select_related('centre', 'responsable')

    if hasattr(request, 'centre_agent') and request.centre_agent:
        base_queryset = base_queryset.filter(centre=request.centre_agent)
    
    miso_filter = MisoFilter(request.GET, queryset=base_queryset)

    context = {
        'filter': miso_filter,
        'titre': "Bibliothèque des Préavis de Maintenance (MISO)",
        'Miso': Miso,
    }
    return render(request, 'technique/liste_miso.html', context)


@login_required
@effective_permission_required('technique.add_miso', raise_exception=True)
def creer_miso_view(request):
    """
    Gère la création d'un nouveau préavis MISO.
    """
    if not hasattr(request.user, 'agent_profile'):
        messages.error(request, "Votre compte utilisateur n'est pas configuré comme un profil Agent.")
        return redirect('technique:liste-miso')

    if request.method == 'POST':
        form = MisoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            miso = form.save(commit=False)
            miso.responsable = request.user.agent_profile
            
            if request.user.agent_profile.centre:
                miso.centre = request.user.agent_profile.centre
            
            if not miso.centre:
                messages.error(request, "Impossible de déterminer le centre pour ce préavis. L'opération a été annulée.")
                return redirect('technique:liste-miso')

            miso.save()

            MisoHistorique.objects.create(
                miso=miso,
                type_evenement=MisoHistorique.TypeEvenement.CREATION,
                auteur=request.user,
                details={'message': f'Création du préavis MISO pour {miso.centre.code_centre}'}
            )

            messages.success(request, f"Le préavis MISO pour {miso.centre.code_centre} a été créé avec succès.")
            return redirect('technique:liste-miso')
    else:
        form = MisoForm(user=request.user)

    context = {
        'form': form,
        'titre': "Créer un Préavis de Maintenance (MISO)",
        'can_edit': True
    }
    return render(request, 'technique/form_miso.html', context)


@login_required
@effective_permission_required('technique.view_miso', raise_exception=True)
def modifier_miso_view(request, miso_id):
    """
    Gère la modification (pour les éditeurs) OU la consultation détaillée (pour les lecteurs)
    d'un MISO existant.
    """
    miso_instance = get_object_or_404(Miso, pk=miso_id)
    
    can_edit = request.user.has_perm('technique.change_miso')

    if request.method == 'POST' and can_edit:
        form = MisoForm(request.POST, request.FILES, instance=miso_instance, user=request.user)
        if form.is_valid():
            form.save()
            MisoHistorique.objects.create(
                miso=miso_instance,
                type_evenement=MisoHistorique.TypeEvenement.MODIFICATION,
                auteur=request.user,
                details={'message': 'Modification des détails du préavis.'}
            )
            messages.success(request, "Le préavis MISO a été mis à jour.")
            return redirect('technique:liste-miso')
    else:
        form = MisoForm(instance=miso_instance, user=request.user)

    if not can_edit:
        for field in form.fields.values():
            field.disabled = True

    context = {
        'form': form,
        'miso': miso_instance,
        'can_edit': can_edit,
        'titre': f"Détail du Préavis MISO du {miso_instance.date_debut.strftime('%d/%m/%Y')}",
    }
    return render(request, 'technique/form_miso.html', context)


@login_required
@effective_permission_required('technique.delete_miso', raise_exception=True)
def annuler_miso_view(request, miso_id):
    """
    Gère l'annulation d'un MISO existant.
    """
    miso_instance = get_object_or_404(Miso, pk=miso_id)

    if request.method == 'POST':
        form = AnnulerMisoForm(request.POST)
        if form.is_valid():
            miso_instance.statut_override = Miso.Statut.ANNULE
            miso_instance.save()

            MisoHistorique.objects.create(
                miso=miso_instance,
                type_evenement=MisoHistorique.TypeEvenement.ANNULATION,
                auteur=request.user,
                details={'motif': form.cleaned_data['motif_annulation']}
            )
            messages.warning(request, f"Le préavis MISO a été annulé.")
            return redirect('technique:liste-miso')
    else:
        form = AnnulerMisoForm()

    context = {
        'form': form,
        'miso': miso_instance,
        'titre': f"Annuler le Préavis MISO du {miso_instance.date_debut.strftime('%d/%m/%Y')}",
    }
    return render(request, 'technique/annuler_miso.html', context)


@login_required
@effective_permission_required('technique.view_miso', raise_exception=True)
def archives_miso_view(request):
    """
    Affiche la liste des MISO archivés (statut ANNULE).
    """
    base_queryset = Miso.objects.filter(statut_override=Miso.Statut.ANNULE).select_related('centre', 'responsable')

    if hasattr(request, 'centre_agent') and request.centre_agent:
        base_queryset = base_queryset.filter(centre=request.centre_agent)
    
    miso_filter = MisoFilter(request.GET, queryset=base_queryset)

    context = {
        'filter': miso_filter,
        'titre': "Archives des Préavis de Maintenance (MISO)",
        'Miso': Miso,
    }
    return render(request, 'technique/archives_miso.html', context)