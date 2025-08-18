
# --- Imports de Django ---
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

# --- Imports de vos applications ---
from core.decorators import effective_permission_required
from suivi.models import Action # Potentiellement nécessaire pour le futur
from ..models import Changement, EtudeSecurite, EtapeEtude
from ..forms import LancerChangementForm, ClassifierChangementForm
from ..filters import EtudeSecuriteFilter



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
def detail_changement_view(request, changement_id):
    changement = get_object_or_404(Changement, pk=changement_id)
    context = {'changement': changement, 'titre': f"Détail du Changement : {changement.titre}"}
    return render(request, 'es/detail_changement.html', context)