# Fichier : es/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Changement, EtudeSecurite, EtapeEtude, CommentaireEtude, MRR
from .forms import LancerChangementForm, ClassifierChangementForm, UploadPreuveForm, CommentaireForm, MRRForm, ActionFormationForm, UpdateEtudeForm
from .filters import EtudeSecuriteFilter
from core.decorators import effective_permission_required
from core.models import Role

from suivi.models import Action
from suivi.services import generer_numero_action


@login_required
def tableau_etudes_view(request):
    """
    Affiche le tableau de bord avec filtres contextuels et explicites.
    """
    # On commence avec une base de données complète
    base_queryset = EtudeSecurite.objects.select_related(
        'changement__initiateur', 
        'changement__correspondant_dircam'
    ).order_by('-created_at')

    # Filtre contextuel : un utilisateur local ne voit que les études de son centre.
    if hasattr(request, 'centre_agent') and request.centre_agent:
        base_queryset = base_queryset.filter(changement__centre_principal=request.centre_agent)
    
    # On applique les filtres explicites soumis par l'utilisateur via le formulaire
    etude_filter = EtudeSecuriteFilter(request.GET, queryset=base_queryset)

    context = {
        'filter': etude_filter, # On passe l'objet filtre complet au template
        'titre': "Tableau de Bord des Études de Sécurité"
    }
    return render(request, 'es/tableau_etudes.html', context)


@login_required
def detail_etude_view(request, etude_id):
    etude = get_object_or_404(
        EtudeSecurite.objects.select_related(
            'changement__initiateur',
            'changement__correspondant_dircam'
        ).prefetch_related('etapes', 'commentaires__auteur', 'mrrs__auteur', 'actions_suivi'),
        pk=etude_id
    )

    update_form = UpdateEtudeForm(instance=etude)

    if request.method == 'POST':
        if 'submit_update_etude' in request.POST:
            form = UpdateEtudeForm(request.POST, instance=etude)
            if form.has_changed():
                if not request.POST.get('commentaire'):
                    form.add_error('commentaire', 'Un commentaire est requis pour toute modification.')
                
                if form.is_valid():
                    ancien_statut = etude.get_statut_display()
                    ancien_avancement = etude.avancement
                    updated_etude = form.save()
                    commentaire_texte = form.cleaned_data['commentaire']
                    
                    CommentaireEtude.objects.create(
                        etude=etude,
                        auteur=request.user.agent_profile,
                        commentaire=f"Mise à jour du pilotage : {commentaire_texte}\n(Statut : {ancien_statut} -> {updated_etude.get_statut_display()}, Avancement : {ancien_avancement}% -> {updated_etude.avancement}%)",
                        piece_jointe=form.cleaned_data.get('piece_jointe')
                    )
                    messages.success(request, "L'étude de sécurité a été mise à jour.")
                    return redirect('es:detail-etude', etude_id=etude.id)
            else:
                messages.info(request, "Aucune modification détectée.")
            update_form = form

        elif 'submit_mrr' in request.POST:
            mrr_form = MRRForm(request.POST)
            if mrr_form.is_valid():
                mrr = mrr_form.save(commit=False)
                mrr.etude = etude
                mrr.auteur = request.user.agent_profile
                mrr.save()
                messages.success(request, "Le MRR a été ajouté à l'étude.")
                return redirect('es:detail-etude', etude_id=etude.id)
        
        elif 'submit_commentaire' in request.POST:
            comment_form = CommentaireForm(request.POST, request.FILES)
            if comment_form.is_valid():
                commentaire = comment_form.save(commit=False)
                commentaire.etude = etude
                commentaire.auteur = request.user.agent_profile
                commentaire.save()
                messages.success(request, "Votre commentaire a été ajouté.")
                return redirect('es:detail-etude', etude_id=etude.id)
    
    mrr_form = MRRForm()
    comment_form = CommentaireForm()
    forms_etapes = {etape.id: UploadPreuveForm(instance=etape) for etape in etude.etapes.all()}
    
    context = {
        'etude': etude,
        'update_form': update_form,
        'etapes': etude.etapes.all(),
        'commentaires': etude.commentaires.all(),
        'forms_etapes': forms_etapes,
        'comment_form': comment_form,
        'mrr_form': mrr_form,
        'actions_suivi_mrr': etude.actions_suivi.filter(categorie=Action.CategorieAction.SUIVI_MRR),
        'titre': f"Étude de Sécurité : {etude.reference_etude}"
    }
    
    return render(request, 'es/detail_etude.html', context)


@login_required
def lancer_changement_view(request):
    if not hasattr(request.user, 'agent_profile'):
        messages.error(request, "Votre compte utilisateur n'est pas lié à un profil Agent.")
        return redirect('es:tableau-etudes')
    if request.method == 'POST':
        form = LancerChangementForm(request.POST, request.FILES)
        if form.is_valid():
            changement = form.save(commit=False)
            changement.initiateur = request.user.agent_profile
            changement.save()
            messages.success(request, f"Le processus de changement '{changement.titre}' a été lancé avec succès et est en attente de classification.")
            return redirect('es:liste-changements')
    else:
        form = LancerChangementForm()
    context = { 'form': form, 'titre': "Lancer un Nouveau Processus de Changement" }
    return render(request, 'core/form_generique.html', context)

@login_required
def classifier_changement_view(request, changement_id):
    changement = get_object_or_404(Changement, pk=changement_id)
    if request.method == 'POST':
        form = ClassifierChangementForm(request.POST, request.FILES, instance=changement)
        if form.is_valid():
            with transaction.atomic():
                updated_changement = form.save()
                if not hasattr(updated_changement, 'etude_securite'):
                    type_etude_choisi = form.cleaned_data['type_etude_requise']
                    nouvelle_etude = EtudeSecurite.objects.create(
                        changement=updated_changement,
                        reference_etude=f"ES-{updated_changement.centre_principal.code_centre}-{updated_changement.created_at.year}-{updated_changement.id:04d}",
                        type_etude=type_etude_choisi
                    )
                    if type_etude_choisi == EtudeSecurite.TypeEtude.DOSSIER_SECURITE:
                        etapes_a_creer = [EtapeEtude.NomEtape.PHASE_PREPARATOIRE, EtapeEtude.NomEtape.FHA, EtapeEtude.NomEtape.PSSA, EtapeEtude.NomEtape.SSA]
                    elif type_etude_choisi == EtudeSecurite.TypeEtude.EPIS:
                        etapes_a_creer = [EtapeEtude.NomEtape.PHASE_PREPARATOIRE, EtapeEtude.NomEtape.SSA]
                    else:
                        etapes_a_creer = []
                    for nom_etape in etapes_a_creer:
                        EtapeEtude.objects.create(etude=nouvelle_etude, nom=nom_etape)
                updated_changement.statut = Changement.StatutProcessus.ETUDE_REQUISE
                updated_changement.save()
            messages.success(request, f"Le changement '{changement.titre}' a été classifié.")
            return redirect('es:detail-etude', etude_id=changement.etude_securite.id)
    else:
        initial_data = {}
        if hasattr(changement, 'etude_securite'):
            initial_data['type_etude_requise'] = changement.etude_securite.type_etude
        form = ClassifierChangementForm(instance=changement, initial=initial_data)
    context = { 'form': form, 'changement': changement, 'titre': f"Classifier le changement : {changement.titre}" }
    return render(request, 'core/form_generique.html', context)

@login_required
def liste_changements_view(request):
    changements_list = Changement.objects.filter(classification=Changement.Classification.NON_DEFINI).select_related('initiateur', 'centre_principal', 'correspondant_dircam').order_by('-created_at')
    context = { 'changements_list': changements_list, 'titre': "Processus de Changement à Classifier" }
    return render(request, 'es/liste_changements.html', context)

@login_required
def uploader_preuve_view(request, etape_id):
    etape = get_object_or_404(EtapeEtude, pk=etape_id)
    if request.method == 'POST':
        form = UploadPreuveForm(request.POST, request.FILES, instance=etape)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le document de preuve pour l'étape '{etape.get_nom_display()}' a été téléversé.")
            return redirect('es:detail-etude', etude_id=etape.etude.id)
    else:
        form = UploadPreuveForm(instance=etape)
    context = { 'form': form, 'etape': etape, 'titre': f"Uploader la preuve pour l'étape : {etape.get_nom_display()}"}
    return render(request, 'core/form_generique.html', context)

@login_required
def valider_etape_view(request, etape_id):
    etape = get_object_or_404(EtapeEtude, pk=etape_id)
    user_agent = request.user.agent_profile
    etude = etape.etude
    changement = etude.changement
    if request.method == 'POST':
        if 'valider_local' in request.POST and user_agent == changement.initiateur:
            etape.validee_par_local = True
            etape.date_validation_local = timezone.now()
            etape.save()
            messages.success(request, f"L'étape '{etape.get_nom_display()}' a été validée par vos soins.")
        if 'valider_national' in request.POST and user_agent == changement.correspondant_dircam:
            with transaction.atomic():
                etape.validee_par_national = True
                etape.date_validation_national = timezone.now()
                etape.save()
                if etape.nom == EtapeEtude.NomEtape.PSSA and etape.mrr_identifies:
                    lignes_mrr = [ligne.strip() for ligne in etape.mrr_identifies.splitlines() if ligne.strip()]
                    for mrr_description in lignes_mrr:
                        numero_action_mrr = generer_numero_action(categorie=Action.CategorieAction.SUIVI_MRR, centre=changement.centre_principal)
                        Action.objects.create(
                            numero_action=numero_action_mrr,
                            titre=f"Suivi MRR ({etude.reference_etude}): {mrr_description}",
                            description=f"Ce moyen de réduction du risque a été identifié lors de l'étude de sécurité {etude.reference_etude}.",
                            categorie=Action.CategorieAction.SUIVI_MRR,
                            responsable=changement.initiateur,
                            echeance=timezone.now().date() + timedelta(days=365),
                            objet_source=etude
                        )
                    if lignes_mrr:
                        messages.info(request, f"{len(lignes_mrr)} action(s) de suivi pour les MRR ont été créées et assignées à {changement.initiateur.trigram}.")
                messages.success(request, f"L'étape '{etape.get_nom_display()}' a été approuvée.")
        return redirect('es:detail-etude', etude_id=etude.id)
    return redirect('es:detail-etude', etude_id=etude.id)
    
@login_required
def creer_action_formation_view(request, etude_id):
    etude = get_object_or_404(EtudeSecurite, pk=etude_id)
    if request.method == 'POST':
        form = ActionFormationForm(request.POST)
        if form.is_valid():
            action = form.save(commit=False)
            action.categorie = Action.CategorieAction.FORMATION
            action.objet_source = etude
            action.numero_action = generer_numero_action(
                categorie=Action.CategorieAction.FORMATION,
                centre=etude.changement.centre_principal
            )
            action.save()
            messages.success(request, f"L'action de formation '{action.titre}' a été créée avec succès.")
            return redirect('es:detail-etude', etude_id=etude.id)
    else:
        form = ActionFormationForm(initial={'titre': f"Formation suite à l'étude {etude.reference_etude}"})
    context = {'form': form, 'etude': etude, 'titre': f"Déclencher une Action de Formation pour l'étude {etude.reference_etude}"}
    return render(request, 'core/form_generique.html', context)

@login_required
def detail_changement_view(request, changement_id):
    changement = get_object_or_404(Changement, pk=changement_id)
    context = {'changement': changement, 'titre': f"Détail du Changement : {changement.titre}"}
    return render(request, 'es/detail_changement.html', context)