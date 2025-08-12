# Fichier : qs/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from core.decorators import effective_permission_required
from core.models import Centre, Role
from .forms import (
    PreDeclarationFNEForm, FNEUpdateOasisForm, FNEClotureForm, 
    RegrouperFNEForm, RapportExterneForm
)
from .services import creer_processus_fne_depuis_pre_declaration
from .models import FNE, DossierEvenement, RapportExterne
from suivi.models import Action, HistoriqueAction
from suivi.forms import UpdateActionForm, AddActionCommentForm
from suivi.services import update_parent_progress


@login_required
def pre_declarer_fne_view(request, centre_id):
    centre = Centre.objects.get(pk=centre_id)
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


def detail_fne_view(request, fne_id):
    fne = get_object_or_404(FNE, pk=fne_id)
    fne_content_type = ContentType.objects.get_for_model(fne)
    action_principale = Action.objects.filter(
        content_type=fne_content_type, object_id=fne.id, parent__isnull=True
    ).first()
    historique_action = action_principale.historique.all().order_by('-timestamp') if action_principale else []
    is_national_view = any(role.role.nom in ['RESPONSABLE_SMS', 'ADJOINT_QS'] for role in request.all_effective_roles)

    # On prépare les instances de formulaires pour le cas GET
    update_oasis_form = FNEUpdateOasisForm(instance=fne)
    cloture_form = FNEClotureForm(instance=fne)
    update_action_form = UpdateActionForm(instance=action_principale)
    add_comment_form = AddActionCommentForm()

    if request.method == 'POST':
        # On teste quel bouton a été soumis et on ne traite QUE le formulaire correspondant
        
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
                update_oasis_form = form # On garde le formulaire invalide pour afficher les erreurs

        elif 'update_action' in request.POST and action_principale:
            form = UpdateActionForm(request.POST, instance=action_principale)
            if form.is_valid():
                update_comment = form.cleaned_data.get('update_comment')
                ancien_statut = action_principale.get_statut_display()
                ancien_avancement = action_principale.avancement
                updated_action = form.save()
                HistoriqueAction.objects.create(
                    action=updated_action, type_evenement=HistoriqueAction.TypeEvenement.CHANGEMENT_AVANCEMENT, 
                    auteur=request.user, details={'ancien_statut': ancien_statut, 'nouveau_statut': updated_action.get_statut_display(), 'ancien_avancement': f"{ancien_avancement}%", 'nouvel_avancement': f"{updated_action.avancement}%", 'commentaire': update_comment }
                )
                messages.success(request, "L'avancement de l'instruction a été mis à jour.")
                return redirect('qs:detail-fne', fne_id=fne.id)
            else:
                update_action_form = form

        elif 'add_comment' in request.POST and action_principale:
            form = AddActionCommentForm(request.POST)
            if form.is_valid():
                commentaire_texte = form.cleaned_data['commentaire']
                HistoriqueAction.objects.create(action=action_principale, type_evenement=HistoriqueAction.TypeEvenement.COMMENTAIRE, auteur=request.user, details={'commentaire': commentaire_texte})
                messages.success(request, "Votre commentaire a été ajouté.")
                return redirect('qs:detail-fne', fne_id=fne.id)
            else:
                add_comment_form = form

        elif 'submit_cloture' in request.POST and is_national_view:
            form = FNEClotureForm(request.POST, request.FILES, instance=fne)
            if form.is_valid():
                with transaction.atomic():
                    clotured_fne = form.save(commit=False)
                    clotured_fne.statut_fne = FNE.StatutFNE.CLOTUREE
                    clotured_fne.save()
                    if action_principale:
                        action_principale.statut = Action.StatutAction.VALIDEE
                        action_principale.save()
                messages.success(request, f"La FNE {clotured_fne.numero_oasis} a été clôturée avec succès.")
                return redirect('qs:detail-fne', fne_id=fne.id)
            else:
                cloture_form = form

    if fne.numero_oasis:
        for field in update_oasis_form.fields.values():
            field.widget.attrs['disabled'] = True

    context = {
        'fne': fne,
        'action_principale': action_principale,
        'historique_action': historique_action,
        'update_oasis_form': update_oasis_form,
        'cloture_form': cloture_form,
        'update_action_form': update_action_form,
        'add_comment_form': add_comment_form,
        'is_national_view': is_national_view,
        'titre': f"Détail FNE : {fne.numero_oasis or '(en attente)'}"
    }
    
    return render(request, 'qs/detail_fne.html', context)

@login_required
def tableau_bord_qs_view(request):
    dossiers_regroupes_ids = DossierEvenement.objects.annotate(
        num_fne=Count('fne_liees')
    ).filter(num_fne__gt=1).values_list('id', flat=True)
    base_queryset = FNE.objects.select_related(
        'centre', 'agent_implique', 'dossier'
    ).prefetch_related(
        'dossier__fne_liees'
    ).order_by('-id')
    is_national_view = any(role.role.nom in ['RESPONSABLE_SMS', 'ADJOINT_QS'] for role in request.all_effective_roles)
    if not is_national_view and hasattr(request, 'centre_agent') and request.centre_agent:
        base_queryset = base_queryset.filter(centre=request.centre_agent)
    context = {
        'fne_list': base_queryset,
        'is_national_view': is_national_view,
        'dossiers_regroupes_ids': list(dossiers_regroupes_ids),
        'titre': "Tableau de Bord - Suivi des FNE",
        'today': timezone.now().date()
    }
    return render(request, 'qs/tableau_bord_qs.html', context)

@login_required
def regrouper_fne_view(request, fne_id_principal):
    fne_principale = get_object_or_404(FNE, pk=fne_id_principal)
    dossier_cible = fne_principale.dossier
    if request.method == 'POST':
        form = RegrouperFNEForm(request.POST, fne_principale=fne_principale)
        if form.is_valid():
            fne_selectionnees = form.cleaned_data['fne_a_regrouper']
            dossiers_originaux_a_verifier = set()
            for fne_a_deplacer in fne_selectionnees:
                dossier_original = fne_a_deplacer.dossier
                dossiers_originaux_a_verifier.add(dossier_original)
                fne_a_deplacer.dossier = dossier_cible
                fne_a_deplacer.save()
            for dossier in dossiers_originaux_a_verifier:
                if dossier.pk != dossier_cible.pk and not dossier.fne_liees.exists():
                    dossier.delete()
            messages.success(request, f"{fne_selectionnees.count()} FNE ont été rattachées avec succès au dossier {dossier_cible.id_girrex}.")
            return redirect('qs:detail-dossier', dossier_id=dossier_cible.id)
    else:
        form = RegrouperFNEForm(fne_principale=fne_principale)
    context = {
        'form': form,
        'fne': fne_principale,
        'titre': f"Regrouper des FNE avec {fne_principale.numero_oasis or fne_principale.id}"
    }
    return render(request, 'core/form_generique.html', context)

@login_required
def ajouter_rapport_externe_view(request, dossier_id):
    dossier = get_object_or_404(DossierEvenement, pk=dossier_id)
    if request.method == 'POST':
        form = RapportExterneForm(request.POST, request.FILES)
        if form.is_valid():
            rapport = form.save(commit=False)
            rapport.dossier = dossier
            rapport.save()
            messages.success(request, "Le rapport externe a été ajouté au dossier.")
            return redirect('qs:detail-dossier', dossier_id=dossier.id)
    else:
        form = RapportExterneForm()
    context = {'form': form, 'dossier': dossier, 'titre': f"Ajouter un rapport externe au dossier {dossier.id_girrex}"}
    return render(request, 'core/form_generique.html', context)

@login_required
def detail_dossier_view(request, dossier_id):
    dossier = get_object_or_404(DossierEvenement, pk=dossier_id)
    fne_liees = dossier.fne_liees.all().select_related('centre', 'agent_implique')
    rapports_externes = dossier.rapports_externes.all()
    context = {
        'dossier': dossier,
        'fne_liees': fne_liees,
        'rapports_externes': rapports_externes,
        'titre': f"Détail du Dossier {dossier.id_girrex}"
    }
    return render(request, 'qs/detail_dossier.html', context)

@login_required
def tableau_bord_qs_national_view(request):
    dossier_list = DossierEvenement.objects.filter(statut_global=DossierEvenement.Statut.OUVERT)
    context = {
        'dossier_list': dossier_list,
        'titre': "Tableau de Bord National QS - Dossiers d'Événements"
    }
    return render(request, 'qs/tableau_bord_qs_national.html', context)

@login_required
def desolidariser_fne_view(request, fne_id):
    fne_a_detacher = get_object_or_404(FNE, pk=fne_id)
    dossier_original = fne_a_detacher.dossier
    if dossier_original.fne_liees.count() <= 1:
        messages.error(request, "Impossible de détacher la dernière FNE d'un dossier.")
        return redirect('qs:detail-dossier', dossier_id=dossier_original.id)
    if request.method == 'POST':
        now = timezone.now()
        new_id_girrex = f"GIRREX-EVT-{now.strftime('%Y%m%d-%H%M%S')}"
        nouveau_dossier = DossierEvenement.objects.create(
            id_girrex=new_id_girrex,
            titre=f"Dossier pour FNE {fne_a_detacher.numero_oasis or fne_a_detacher.id} (détachée)",
            date_evenement=dossier_original.date_evenement
        )
        fne_a_detacher.dossier = nouveau_dossier
        fne_a_detacher.save()
        messages.success(request, f"La FNE {fne_a_detacher.numero_oasis or fne_a_detacher.id} a été détachée avec succès dans un nouveau dossier.")
        return redirect('qs:detail-dossier', dossier_id=dossier_original.id)
    return redirect('qs:detail-dossier', dossier_id=dossier_original.id)