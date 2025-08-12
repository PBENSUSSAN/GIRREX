# Fichier : suivi/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from .models import Action, HistoriqueAction, PriseEnCompte
from .forms import CreateActionForm, UpdateActionForm, AddActionCommentForm, DiffusionForm
from .services import update_parent_progress, final_close_action_cascade, creer_diffusion
from core.models import AgentRole, Role
from documentation.models import Document, DocumentPriseEnCompte
from .filters import ActionFilter, ArchiveFilter
from qs.models import FNE, HistoriqueFNE
from qs.audit import log_audit_fne

def user_has_role(user, role_name):
    """ Vérifie si un utilisateur a un rôle métier spécifique et actif. """
    if not hasattr(user, 'agent_profile'):
        return False
    return AgentRole.objects.filter(
        agent=user.agent_profile,
        role__nom=role_name,
        date_fin__isnull=True
    ).exists()

@login_required
def tableau_actions_view(request):
    """
    Affiche le tableau de suivi de manière hiérarchique.
    """
    base_queryset = Action.objects.for_user(request.user).select_related(
        'responsable', 'parent'
    ).prefetch_related(
        'sous_taches__responsable',
        'sous_taches__prise_en_compte',
        'centres'
    )
    
    action_filter = ActionFilter(request.GET, queryset=base_queryset)
    actions_meres = action_filter.qs.filter(parent__isnull=True)
    
    context = {
        'filter': action_filter,
        'actions_meres': actions_meres,
        'titre': "Tableau de Suivi des Actions"
    }
    return render(request, 'suivi/tableau_actions.html', context)

@login_required
def create_action_view(request):
    """
    Gère la création d'une nouvelle action générique (non-documentaire).
    """
    if request.method == 'POST':
        form = CreateActionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            action = form.save()
            # La méthode save() du formulaire ModelForm gère les ManyToMany si commit=True
            messages.success(request, f"L'action '{action.numero_action}' a été créée.")
            return redirect('suivi:tableau-actions')
    else:
        form = CreateActionForm(user=request.user)

    context = { 'form': form, 'titre': "Créer une nouvelle action" }
    return render(request, 'suivi/create_action.html', context)

@login_required
def detail_action_view(request, action_id):
    """
    Affiche le détail d'une action, son historique et les formulaires d'interaction.
    """
    action = get_object_or_404(Action.archives.select_related('responsable', 'parent'), pk=action_id)
    historique = action.historique.all().order_by('-timestamp')
    update_form = UpdateActionForm(instance=action)
    comment_form = AddActionCommentForm()

    if request.method == 'POST':
        if 'update_action' in request.POST:
            update_form = UpdateActionForm(request.POST, instance=action)
            if update_form.is_valid():
                ancien_statut = action.get_statut_display()
                ancien_avancement = action.avancement
                updated_action = update_form.save()
                if updated_action.parent:
                    update_parent_progress(updated_action)
                
                # Étape 1 : On enregistre l'historique dans suivi (comportement normal)
                HistoriqueAction.objects.create(
                    action=updated_action, type_evenement=HistoriqueAction.TypeEvenement.CHANGEMENT_AVANCEMENT, auteur=request.user,
                    details={ 'ancien_statut': ancien_statut, 'nouveau_statut': updated_action.get_statut_display(), 'ancien_avancement': f"{ancien_avancement}%", 'nouvel_avancement': f"{updated_action.avancement}%", 'commentaire': update_form.cleaned_data.get('update_comment') }
                )

                # Étape 2 : On vérifie la nature de la tâche et on envoie à l'audit si nécessaire
                if isinstance(updated_action.objet_source, FNE):
                    log_audit_fne(
                        fne=updated_action.objet_source,
                        type_evenement=HistoriqueFNE.TypeEvenement.CHANGEMENT_STATUT_INSTRUCTION,
                        auteur=request.user,
                        details={
                            'ancien_statut': ancien_statut, 
                            'nouveau_statut': updated_action.get_statut_display(), 
                            'ancien_avancement': f"{ancien_avancement}%", 
                            'nouvel_avancement': f"{updated_action.avancement}%", 
                            'commentaire': update_form.cleaned_data.get('update_comment')
                        }
                    )

                messages.success(request, "L'action a été mise à jour.")
                return redirect('suivi:detail-action', action_id=action.id)
        
        elif 'add_comment' in request.POST:
            comment_form = AddActionCommentForm(request.POST)
            if comment_form.is_valid():
                commentaire_texte = comment_form.cleaned_data['commentaire']
                
                # Étape 1 : On enregistre l'historique dans suivi
                HistoriqueAction.objects.create(action=action, type_evenement=HistoriqueAction.TypeEvenement.COMMENTAIRE, auteur=request.user, details={'commentaire': commentaire_texte})

                # Étape 2 : On vérifie la nature de la tâche et on envoie à l'audit
                if isinstance(action.objet_source, FNE):
                    log_audit_fne(
                        fne=action.objet_source,
                        type_evenement=HistoriqueFNE.TypeEvenement.COMMENTAIRE,
                        auteur=request.user,
                        details={'commentaire': commentaire_texte}
                    )

                messages.success(request, "Votre commentaire a été ajouté.")
                return redirect('suivi:detail-action', action_id=action.id)
    
    is_initiateur_action_mere = False
    if action.parent and request.user.agent_profile == action.parent.responsable:
        is_initiateur_action_mere = True
    elif not action.parent and request.user.agent_profile == action.responsable:
        is_initiateur_action_mere = True

    context = {
        'action': action, 'historique': historique, 'update_form': update_form, 'comment_form': comment_form,
        'titre': f"Action : {action.numero_action or action.titre}",
        'is_responsable_sms': user_has_role(request.user, Role.RoleName.RESPONSABLE_SMS),
        'is_initiateur_action_mere': is_initiateur_action_mere
    }
    return render(request, 'suivi/detail_action.html', context)

@login_required
def lancer_diffusion_view(request, content_type_id, object_id):
    """
    Affiche le formulaire de paramétrage de la diffusion et appelle le service métier.
    """
    try:
        content_type = get_object_or_404(ContentType, pk=content_type_id)
        objet_source = content_type.get_object_for_this_type(pk=object_id)
    except Http404:
        messages.error(request, "L'objet que vous essayez de diffuser n'existe pas ou est inaccessible.")
        return redirect('home')

    if request.method == 'POST':
        form = DiffusionForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    action_mere = creer_diffusion(
                        objet_source=objet_source,
                        initiateur=request.user.agent_profile,
                        form_data=form.cleaned_data
                    )
                messages.success(request, f"La diffusion a été lancée avec succès. L'action mère '{action_mere.numero_action}' a été créée.")
                return redirect('suivi:detail-action', action_id=action_mere.id)
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de la création des tâches : {e}")
    else:
        form = DiffusionForm(user=request.user)

    context = {
        'form': form,
        'objet_source': objet_source,
        'titre': f"Paramètres de diffusion pour : {objet_source}"
    }
    return render(request, 'suivi/lancer_diffusion.html', context)

@login_required
def valider_prise_en_compte_view(request, action_id):
    action_agent = get_object_or_404(Action, pk=action_id)
    if action_agent.responsable != request.user.agent_profile:
        messages.error(request, "Vous n'êtes pas le responsable de cette action.")
        return redirect('suivi:detail-action', action_id=action_agent.id)
    try:
        with transaction.atomic():
            # La logique existante pour le suivi de la tâche est conservée
            PriseEnCompte.objects.get_or_create(action_agent=action_agent, defaults={'agent': request.user.agent_profile})
            action_agent.statut = Action.StatutAction.VALIDEE
            action_agent.avancement = 100
            action_agent.save()
            update_parent_progress(action_agent)

            # On vérifie si l'objet source de l'action est bien un Document
            # C'est cette vérification qui garantit la généricité de votre module de suivi.
            if isinstance(action_agent.objet_source, Document):
                document_concerne = action_agent.objet_source
                # On crée l'enregistrement d'audit dans notre nouveau modèle.
                # get_or_create est parfait car il évite les doublons si l'action est
                # validée plusieurs fois par erreur.
                DocumentPriseEnCompte.objects.get_or_create(
                    document=document_concerne,
                    agent=request.user.agent_profile
                )

        messages.success(request, "Votre prise en compte a bien été enregistrée.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {e}")
    return redirect('suivi:tableau-actions')

@login_required
def valider_etape_responsable_view(request, action_id):
    action = get_object_or_404(Action, pk=action_id)
    if action.responsable != request.user.agent_profile:
        messages.error(request, "Vous n'êtes pas le responsable de cette action.")
        return redirect('suivi:detail-action', action_id=action.id)
    if action.statut != Action.StatutAction.A_VALIDER:
        messages.warning(request, "Cette action n'est pas prête à être validée.")
        return redirect('suivi:detail-action', action_id=action.id)
    try:
        with transaction.atomic():
            ancien_statut_display = action.get_statut_display()
            action.statut = Action.StatutAction.VALIDEE
            action.save()
            HistoriqueAction.objects.create(action=action, type_evenement=HistoriqueAction.TypeEvenement.CHANGEMENT_STATUT, auteur=request.user, details={'ancien': ancien_statut_display, 'nouveau': action.get_statut_display()})
            if action.parent:
                update_parent_progress(action)
        messages.success(request, f"L'étape '{action.titre}' a été validée.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {e}")
    return redirect('suivi:tableau-actions')
    
@login_required
def cloture_initiateur_view(request, action_id):
    action = get_object_or_404(Action, pk=action_id)
    if request.user.agent_profile != action.responsable:
        messages.error(request, "Seul le responsable de l'action peut effectuer la clôture finale.")
        return redirect('suivi:detail-action', action_id=action.id)
    try:
        final_close_action_cascade(action, request.user)
        messages.success(request, f"L'action '{action.numero_action}' et ses sous-tâches ont été clôturées à 100%.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {e}")
    return redirect('suivi:tableau-actions')

@login_required
def cloture_finale_sms_view(request, action_id):
    action = get_object_or_404(Action, pk=action_id)
    if not user_has_role(request.user, Role.RoleName.RESPONSABLE_SMS):
        messages.error(request, "Seul un Responsable SMS peut effectuer la clôture finale.")
        return redirect('suivi:detail-action', action_id=action.id)
    try:
        final_close_action_cascade(action, request.user)
        messages.success(request, "L'action et toutes ses sous-tâches ont été clôturées à 100%.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {e}")
    return redirect('suivi:tableau-actions')

@login_required
def archiver_actions_view(request):
    if request.method == 'POST':
        action_ids_a_archiver = request.POST.getlist('actions_a_archiver')
        actions_validees = Action.objects.for_user(request.user).filter(pk__in=action_ids_a_archiver, statut=Action.StatutAction.VALIDEE)
        count = actions_validees.update(statut=Action.StatutAction.ARCHIVEE)
        messages.success(request, f"{count} action(s) ont été archivées.")
    return redirect('suivi:tableau-actions')

@login_required
def archives_actions_view(request):
    visible_archives = Action.archives.for_user(request.user).filter(statut=Action.StatutAction.ARCHIVEE)
    archive_filter = ArchiveFilter(request.GET, queryset=visible_archives)
    context = {
        'filter': archive_filter,
        'titre': "Archives des Actions"
    }
    return render(request, 'suivi/archives_actions.html', context)