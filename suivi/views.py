# Fichier : suivi/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, models

from .models import Action, HistoriqueAction, PriseEnCompte
from .forms import CreateActionForm, UpdateActionForm, AddActionCommentForm, DiffusionCibleForm
from .services import update_parent_progress, final_close_action_cascade
from core.models import Agent, AgentRole, Centre
from .filters import ActionFilter

from documentation.models import Document, VersionDocument, DocumentType

def user_has_role(user, role_name):
    if not hasattr(user, 'agent_profile'): return False
    return AgentRole.objects.filter(agent=user.agent_profile, role__nom=role_name, date_fin__isnull=True).exists()

@login_required
def tableau_actions_view(request):
    """
    Affiche le tableau de suivi de manière hiérarchique.
    Seules les actions mères sont affichées au premier niveau.
    """
    # On récupère la base de toutes les actions visibles par l'utilisateur
    base_queryset = Action.objects.for_user(request.user).select_related(
        'responsable', 'centre', 'parent'
    ).prefetch_related(
        'sous_taches__responsable' # Optimisation pour charger les sous-tâches
    )
    
    # On applique les filtres sur l'ensemble des actions
    action_filter = ActionFilter(request.GET, queryset=base_queryset)
    
    # On ne garde que les actions "mères" pour l'affichage principal
    # Les sous-tâches seront accessibles via la relation pré-chargée
    actions_meres = action_filter.qs.filter(parent__isnull=True)
    
    context = {
        'filter': action_filter,
        'actions_meres': actions_meres, # On passe cette nouvelle variable au template
        'titre': "Tableau de Suivi des Actions"
    }
    return render(request, 'suivi/tableau_actions.html', context)

@login_required
def create_action_view(request):
    if request.method == 'POST':
        # On passe request.FILES pour gérer l'upload
        form = CreateActionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Le code de sauvegarde ne s'exécute QUE si le formulaire est valide
            try:
                with transaction.atomic():
                    action = form.save(commit=False)
                    if request.user.agent_profile and request.user.agent_profile.centre:
                        action.centre = request.user.agent_profile.centre
                    
                    if action.categorie == Action.CategorieAction.DIFFUSION_DOC:
                        doc_type, _ = DocumentType.objects.get_or_create(nom="Document Externe")
                        document = Document.objects.create(
                            intitule=form.cleaned_data['document_intitule'],
                            reference=f"MANUEL-{timezone.now().strftime('%Y%m%d-%H%M%S')}",
                            type_document=doc_type,
                            responsable_suivi=action.responsable
                        )
                        version = VersionDocument.objects.create(
                            document=document,
                            numero_version="1.0",
                            fichier_pdf=form.cleaned_data['piece_jointe'],
                            enregistre_par=request.user,
                            _creation_manuelle=True
                        )
                        action.objet_source = version
                    
                    action.save()
                    messages.success(request, f"L'action '{action.numero_action}' a été créée.")
                    return redirect('suivi:tableau-actions')
            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {e}")
        # Si le formulaire n'est PAS valide, on ne fait rien ici.
        # La vue continuera jusqu'en bas et ré-affichera le formulaire
        # avec les erreurs.
    else:
        form = CreateActionForm(user=request.user)

    context = {
        'form': form,
        'titre': "Créer une nouvelle action"
    }
    return render(request, 'suivi/create_action.html', context)

@login_required
def detail_action_view(request, action_id):
    action = get_object_or_404(Action, pk=action_id)
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
                HistoriqueAction.objects.create(
                    action=updated_action,
                    type_evenement=HistoriqueAction.TypeEvenement.CHANGEMENT_AVANCEMENT,
                    auteur=request.user,
                    details={
                        'ancien_statut': ancien_statut, 'nouveau_statut': updated_action.get_statut_display(),
                        'ancien_avancement': f"{ancien_avancement}%", 'nouvel_avancement': f"{updated_action.avancement}%",
                        'commentaire': update_form.cleaned_data.get('update_comment')
                    }
                )
                messages.success(request, "L'action a été mise à jour.")
                return redirect('suivi:detail-action', action_id=action.id)
        elif 'add_comment' in request.POST:
            comment_form = AddActionCommentForm(request.POST)
            if comment_form.is_valid():
                commentaire_texte = comment_form.cleaned_data['commentaire']
                HistoriqueAction.objects.create(
                    action=action, type_evenement=HistoriqueAction.TypeEvenement.COMMENTAIRE,
                    auteur=request.user, details={'commentaire': commentaire_texte}
                )
                messages.success(request, "Votre commentaire a été ajouté.")
                return redirect('suivi:detail-action', action_id=action.id)
    
    context = {
        'action': action, 'historique': historique,
        'update_form': update_form, 'comment_form': comment_form,
        'titre': f"Action : {action.numero_action}",
        'is_responsable_sms': user_has_role(request.user, "Responsable SMS")
    }
    return render(request, 'suivi/detail_action.html', context)

# --- VUES DE WORKFLOW ---

@login_required
def dispatch_action_view(request, action_id, target_role_name=None):
    action_parente = get_object_or_404(Action, pk=action_id)
    if action_parente.statut != Action.StatutAction.A_FAIRE:
        messages.warning(request, "Cette action a déjà été diffusée ou est en cours de traitement.")
        return redirect('suivi:detail-action', action_id=action_parente.id)

    if request.method == 'POST':
        form = DiffusionCibleForm(request.POST)
        if form.is_valid():
            centres_selectionnes = form.cleaned_data['centres']
            agents_cibles = []

            if target_role_name:
                roles = AgentRole.objects.filter(centre__in=centres_selectionnes, role__nom=target_role_name, date_fin__isnull=True).select_related('agent')
                agents_cibles = [role.agent for role in roles]
                titre_sous_tache = action_parente.titre
                categorie_sous_tache = action_parente.categorie
            else:
                agents_cibles = Agent.objects.filter(centre__in=centres_selectionnes, actif=True)
                version_doc = action_parente.objet_source
                titre_sous_tache = f"Prise en compte : {version_doc.document.reference} v{version_doc.numero_version}"
                categorie_sous_tache = Action.CategorieAction.PRISE_EN_COMPTE_DOC

            try:
                with transaction.atomic():
                    action_parente.statut = Action.StatutAction.EN_COURS
                    action_parente.avancement = 25
                    action_parente.save()

                    now_str = timezone.now().strftime('%d/%m/%Y à %H:%M')
                    nom_centres = ", ".join([c.code_centre for c in centres_selectionnes])
                    HistoriqueAction.objects.create(
                        action=action_parente,
                        type_evenement=HistoriqueAction.TypeEvenement.COMMENTAIRE,
                        auteur=request.user,
                        details={'commentaire': f"Diffusion lancée le {now_str} vers le(s) centre(s) : {nom_centres}."}
                    )
                    
                    # LA CORRECTION D'INDENTATION EST ICI
                    for agent in agents_cibles:
                        if not Action.objects.filter(parent=action_parente, responsable=agent).exists():
                            Action.objects.create(
                                parent=action_parente, titre=titre_sous_tache, responsable=agent,
                                echeance=action_parente.echeance, objet_source=action_parente.objet_source,
                                categorie=categorie_sous_tache
                            )
                
                messages.success(request, f"L'action a été diffusée à {len(agents_cibles)} destinataire(s).")
                return redirect('suivi:detail-action', action_id=action_parente.id)
            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {e}")
    else:
        form = DiffusionCibleForm()

    context = {
        'form': form, 'action': action_parente,
        'titre': f"Diffuser l'action : {action_parente.titre}"
    }
    return render(request, 'suivi/dispatch_action.html', context)

@login_required
def diffuser_aux_animateurs_qs_view(request, action_id):
    return dispatch_action_view(request, action_id, target_role_name="Animateur QS")

@login_required
def lancer_diffusion_agents_view(request, action_id):
    return dispatch_action_view(request, action_id, target_role_name=None)

@login_required
def valider_prise_en_compte_view(request, action_id):
    action_agent = get_object_or_404(Action, pk=action_id)
    if action_agent.responsable != request.user.agent_profile:
        messages.error(request, "Vous n'êtes pas le responsable de cette action.")
        return redirect('suivi:detail-action', action_id=action_agent.id)
    try:
        with transaction.atomic():
            PriseEnCompte.objects.get_or_create(
                action_agent=action_agent,
                defaults={'agent': request.user.agent_profile}
            )
            action_agent.statut = Action.StatutAction.VALIDEE
            action_agent.avancement = 100
            action_agent.save()
            update_parent_progress(action_agent)
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
            HistoriqueAction.objects.create(
                action=action, type_evenement=HistoriqueAction.TypeEvenement.CHANGEMENT_STATUT,
                auteur=request.user, details={'ancien': ancien_statut_display, 'nouveau': action.get_statut_display()}
            )
            if action.parent:
                update_parent_progress(action)
        messages.success(request, f"L'étape '{action.titre}' a été validée.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {e}")
    return redirect('suivi:tableau-actions')

@login_required
def cloture_finale_sms_view(request, action_id):
    action = get_object_or_404(Action, pk=action_id)
    if not user_has_role(request.user, "Responsable SMS"):
        messages.error(request, "Seul un Responsable SMS peut effectuer la clôture finale.")
        return redirect('suivi:detail-action', action_id=action.id)
    try:
        final_close_action_cascade(action, request.user)
        messages.success(request, "L'action et toutes ses sous-tâches ont été clôturées à 100%.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {e}")
    return redirect('suivi:tableau-actions')