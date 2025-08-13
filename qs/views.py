# Fichier : qs/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.db.models import Count

from core.decorators import effective_permission_required
from core.models import Centre, Role
from .forms import (
    PreDeclarationFNEForm, FNEUpdateOasisForm, FNEClotureForm,
    RapportExterneForm, RecommendationQSForm # On ajoute l'import du nouveau formulaire
)
from .services import creer_processus_fne_depuis_pre_declaration
from .models import FNE, RapportExterne, RecommendationQS # On ajoute l'import de RecommendationQS
from suivi.models import Action
from qs.audit import log_audit_fne

@login_required
@effective_permission_required('qs.add_fne', raise_exception=True)
def pre_declarer_fne_view(request, centre_id):
    centre = get_object_or_404(Centre, pk=centre_id)
    if request.method == 'POST':
        form = PreDeclarationFNEForm(request.POST, centre=centre)
        if form.is_valid():
            try:
                with transaction.atomic():
                    creer_processus_fne_depuis_pre_declaration(
                        agent_implique=form.cleaned_data['agent_implique'],
                        description=form.cleaned_data['description'],
                        centre=centre,
                        createur=request.user
                    )
                    messages.success(request, "Pré-déclaration de FNE enregistrée avec succès. Les tâches de suivi ont été créées.")
                return redirect('cahier-de-marche', centre_id=centre.id, jour=timezone.now().strftime('%Y-%m-%d'))
            except Exception as e:
                messages.error(request, f"Une erreur inattendue est survenue : {e}")
    else:
        form = PreDeclarationFNEForm(centre=centre)
    context = {'form': form, 'centre': centre, 'titre': "Pré-déclarer un événement QS"}
    return render(request, 'core/form_generique.html', context)


@login_required
@effective_permission_required('qs.view_fne', raise_exception=True)
def detail_fne_view(request, fne_id):
    fne = get_object_or_404(
        FNE.objects.select_related('centre', 'agent_implique').prefetch_related('rapports_externes', 'recommendations'), 
        pk=fne_id
    )
    historique_permanent = fne.historique_permanent.select_related('auteur').order_by('-timestamp')

    action_principale = Action.objects.filter(
        object_id=fne.id,
        content_type__model='fne',
        parent__isnull=True
    ).select_related('responsable').first()

    is_national_view = any(role.role.nom in [Role.RoleName.RESPONSABLE_SMS, Role.RoleName.ADJOINT_QS] for role in request.all_effective_roles)
    
    update_oasis_form = FNEUpdateOasisForm(instance=fne)
    cloture_form = FNEClotureForm(instance=fne)

    if request.method == 'POST':
        if 'submit_oasis' in request.POST:
            form = FNEUpdateOasisForm(request.POST, instance=fne)
            if form.is_valid():
                with transaction.atomic():
                    updated_fne = form.save(commit=False)
                    updated_fne.statut_fne = FNE.StatutFNE.INSTRUCTION_EN_COURS
                    updated_fne.save()
                    if action_principale:
                        action_principale.titre = f"Instruire et clôturer FNE ({updated_fne.numero_oasis})"
                        action_principale.avancement = 10
                        action_principale.statut = Action.StatutAction.EN_COURS
                        action_principale.save()
                        tache_agent = action_principale.sous_taches.first()
                        if tache_agent:
                            tache_agent.statut = Action.StatutAction.VALIDEE
                            tache_agent.save()
                messages.success(request, "Infos OASIS enregistrées. L'instruction peut commencer.")
                return redirect('qs:detail-fne', fne_id=fne.id)
            else:
                update_oasis_form = form

        elif 'submit_cloture' in request.POST and is_national_view:
            form = FNEClotureForm(request.POST, request.FILES, instance=fne)
            if form.is_valid():
                with transaction.atomic():
                    clotured_fne = form.save(commit=False)
                    clotured_fne.statut_fne = FNE.StatutFNE.CLOTUREE
                    clotured_fne.save()
                    if action_principale:
                        action_principale.statut = Action.StatutAction.VALIDEE
                        action_principale.avancement = 100
                        action_principale.save()
                messages.success(request, f"La FNE {clotured_fne.numero_oasis} a été clôturée avec succès.")
                return redirect('qs:detail-fne', fne_id=fne.id)
            else:
                cloture_form = form

    context = {
        'fne': fne,
        'rapports_externes': fne.rapports_externes.all(),
        'action_principale': action_principale,
        'historique_permanent': historique_permanent,
        'update_oasis_form': update_oasis_form,
        'cloture_form': cloture_form,
        'is_national_view': is_national_view,
        'titre': f"Détail FNE : {fne.titre or '(en attente)'}"
    }
    
    return render(request, 'qs/detail_fne.html', context)

@login_required
@effective_permission_required('qs.view_fne', raise_exception=True)
def tableau_bord_qs_view(request):
    base_queryset = FNE.objects.select_related('centre', 'agent_implique').order_by('-id')
    
    is_national_view = any(role.role.nom in [Role.RoleName.RESPONSABLE_SMS, Role.RoleName.ADJOINT_QS] for role in request.all_effective_roles)
    if not is_national_view and hasattr(request, 'centre_agent') and request.centre_agent:
        base_queryset = base_queryset.filter(centre=request.centre_agent)
        
    context = {
        'fne_list': base_queryset,
        'is_national_view': is_national_view,
        'titre': "Tableau de Bord - Suivi des FNE",
        'today': timezone.now().date()
    }
    return render(request, 'qs/tableau_bord_qs.html', context)

@login_required
@effective_permission_required('qs.add_rapportexterne', raise_exception=True)
def ajouter_rapport_externe_view(request, fne_id):
    fne = get_object_or_404(FNE, pk=fne_id)
    if request.method == 'POST':
        form = RapportExterneForm(request.POST, request.FILES)
        if form.is_valid():
            rapport = form.save(commit=False)
            rapport.fne = fne
            rapport.save()
            messages.success(request, "Le rapport externe a été ajouté à la FNE.")
            return redirect('qs:detail-fne', fne_id=fne.id)
    else:
        form = RapportExterneForm()
    context = {'form': form, 'fne': fne, 'titre': f"Ajouter un rapport externe à la FNE {fne.id_girrex}"}
    return render(request, 'core/form_generique.html', context)

# ==============================================================================
#                 DÉBUT DE L'AJOUT DE LA NOUVELLE VUE
# ==============================================================================
@login_required
@effective_permission_required('qs.add_recommendationqs', raise_exception=True)
def ajouter_recommandation_view(request, fne_id):
    """
    Gère la création d'une nouvelle recommandation QS liée à une FNE.
    """
    fne = get_object_or_404(FNE, pk=fne_id)
    if request.method == 'POST':
        form = RecommendationQSForm(request.POST)
        if form.is_valid():
            reco = form.save(commit=False)
            reco.source = fne  # On lie la recommandation à la FNE via la GenericForeignKey
            reco.save()
            messages.success(request, "La recommandation a été ajoutée avec succès.")
            return redirect('qs:detail-fne', fne_id=fne.id)
    else:
        form = RecommendationQSForm()
    
    context = {
        'form': form,
        'fne': fne, # On passe la fne pour afficher des infos contextuelles
        'titre': f"Ajouter une recommandation pour la FNE {fne.id_girrex}"
    }
    # On peut réutiliser le template générique, mais il serait mieux d'en créer un dédié.
    # Pour l'instant, utilisons le générique.
    return render(request, 'core/form_generique.html', context)
# ==============================================================================
#                   FIN DE L'AJOUT DE LA NOUVELLE VUE
# ==============================================================================