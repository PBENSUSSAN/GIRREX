# Fichier : es/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Changement, EtudeSecurite, EtapeEtude, CommentaireEtude
from .forms import LancerChangementForm, ClassifierChangementForm, UploadPreuveForm, CommentaireForm
from core.decorators import effective_permission_required
from core.models import Role

@login_required
def tableau_etudes_view(request):
    etudes_list = EtudeSecurite.objects.select_related('changement__initiateur', 'changement__correspondant_dircam').order_by('-created_at')
    context = { 'etudes_list': etudes_list, 'titre': "Tableau de Bord des Études de Sécurité" }
    return render(request, 'es/tableau_etudes.html', context)

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

# ==========================================================
#              VUE DE CLASSIFICATION CORRIGÉE
# ==========================================================
@login_required
def classifier_changement_view(request, changement_id):
    changement = get_object_or_404(Changement, pk=changement_id)

    if request.method == 'POST':
        form = ClassifierChangementForm(request.POST, request.FILES, instance=changement)
        if form.is_valid():
            with transaction.atomic():
                # On sauvegarde juste la classification et le fichier de réponse sur l'objet Changement.
                updated_changement = form.save()
                
                # Maintenant, la vue prend le contrôle de la création de l'étude.
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

                # On met à jour le statut du changement pour le faire sortir de la liste "à classifier"
                updated_changement.statut = Changement.StatutProcessus.ETUDE_REQUISE
                updated_changement.save()

            messages.success(request, f"Le changement '{changement.titre}' a été classifié. L'étude de sécurité a été créée.")
            return redirect('es:detail-etude', etude_id=changement.etude_securite.id)
    else:
        initial_data = {}
        if hasattr(changement, 'etude_securite'):
            initial_data['type_etude_requise'] = changement.etude_securite.type_etude
        form = ClassifierChangementForm(instance=changement, initial=initial_data)

    context = { 'form': form, 'changement': changement, 'titre': f"Classifier le changement : {changement.titre}" }
    return render(request, 'core/form_generique.html', context)

# ... (le reste des vues : detail_etude_view, etc. restent les mêmes pour l'instant) ...

@login_required
def detail_etude_view(request, etude_id):
    etude = get_object_or_404(EtudeSecurite.objects.select_related('changement__initiateur', 'changement__correspondant_dircam').prefetch_related('etapes', 'commentaires__auteur'), pk=etude_id)
    context = {'etude': etude, 'etapes': etude.etapes.all(), 'commentaires': etude.commentaires.all(), 'titre': f"Étude de Sécurité : {etude.reference_etude}"}
    return render(request, 'es/detail_etude.html', context)

# ==========================================================
#         VUE DE LA LISTE DES CHANGEMENTS CORRIGÉE
# ==========================================================
@login_required
def liste_changements_view(request):
    """
    Affiche la liste des processus de changement qui n'ont pas encore été classifiés.
    """
    # La requête filtre maintenant sur la classification et non plus sur le statut.
    changements_list = Changement.objects.filter(
        classification=Changement.Classification.NON_DEFINI
    ).select_related('initiateur', 'centre_principal', 'correspondant_dircam').order_by('-created_at')

    context = { 'changements_list': changements_list, 'titre': "Processus de Changement à Classifier" }
    return render(request, 'es/liste_changements.html', context)

# ... (le reste des vues pour uploader, valider, commenter) ...
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
            etape.validee_par_national = True
            etape.date_validation_national = timezone.now()
            etape.save()
            messages.success(request, f"L'étape '{etape.get_nom_display()}' a été approuvée.")
        return redirect('es:detail-etude', etude_id=etude.id)
    return redirect('es:detail-etude', etude_id=etude.id)

@login_required
def ajouter_commentaire_view(request, etude_id):
    etude = get_object_or_404(EtudeSecurite, pk=etude_id)
    if request.method == 'POST':
        form = CommentaireForm(request.POST, request.FILES)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.etude = etude
            commentaire.auteur = request.user.agent_profile
            commentaire.save()
            messages.success(request, "Votre commentaire a été ajouté.")
    return redirect('es:detail-etude', etude_id=etude.id)