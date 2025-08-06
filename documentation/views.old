# Fichier : documentation/views.py (Version MISE À JOUR pour diffusion explicite)

# --- Imports Django natifs ---
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import FileResponse, Http404
from django.urls import reverse
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

# --- Imports depuis nos applications ---
from .models import Document, VersionDocument
from .forms import AddVersionForm, DocumentForm
from core.models import AgentRole, Role # MODIFIÉ : Ajout de l'import de Role
from suivi.models import Action
from .filters import DocumentFilter

# ==============================================================================
# Vues de consultation de la bibliothèque
# ==============================================================================

@login_required
def liste_documents_view(request):
    """
    Affiche la liste des documents actifs, en appliquant les filtres
    et en pré-chargeant les versions pour un affichage optimisé.
    """
    # On garde la même base de documents
    base_queryset = Document.objects.filter(
        statut_suivi__in=['A_JOUR', 'EN_REDACTION', 'RENOUVELLEMENT_PLANIFIE', 'PERIME']
    ).prefetch_related('versions') # MODIFIÉ : Optimisation pour charger les versions efficacement

    document_filter = DocumentFilter(request.GET, queryset=base_queryset)
    
    context = {
        'filter': document_filter,
        'titre': "Bibliothèque Documentaire"
    }
    return render(request, 'documentation/liste_documents.html', context)

@login_required
def detail_document_view(request, document_id):
    """ Affiche les détails d'un document et la liste de ses versions. """
    document = get_object_or_404(Document, pk=document_id)
    versions = document.versions.all().order_by('-date_mise_en_vigueur')
    context = { 'document': document, 'versions': versions, 'titre': f"Détail : {document.reference}" }
    return render(request, 'documentation/detail_document.html', context)

# ==============================================================================
# Vues de gestion des fichiers PDF
# ==============================================================================

@login_required
def view_pdf_view(request, version_id):
    """ Sert le fichier PDF pour qu'il soit affiché ("inline") dans le navigateur. """
    version = get_object_or_404(VersionDocument, pk=version_id)
    try:
        return FileResponse(version.fichier_pdf.open('rb'), as_attachment=False, content_type='application/pdf')
    except FileNotFoundError:
        raise Http404("Le fichier PDF n'a pas été trouvé sur le serveur.")

@login_required
def download_pdf_view(request, version_id):
    """ Sert le fichier PDF pour forcer son téléchargement ("attachment"). """
    version = get_object_or_404(VersionDocument, pk=version_id)
    try:
        return FileResponse(version.fichier_pdf.open('rb'), as_attachment=True, content_type='application/pdf')
    except FileNotFoundError:
        raise Http404("Le fichier PDF n'a pas été trouvé sur le serveur.")

# ==============================================================================
# Vue pour l'ajout d'une nouvelle version (MODIFIÉE)
# ==============================================================================

@login_required
# @permission_required('documentation.add_versiondocument', raise_exception=True)
def add_version_view(request, document_id):
    """ Gère le formulaire et la logique pour ajouter une nouvelle version à un document. """
    document = get_object_or_404(Document, pk=document_id)
    
    if request.method == 'POST':
        form = AddVersionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Préparation de la nouvelle version
                    new_version = form.save(commit=False)
                    new_version.document = document
                    new_version.enregistre_par = request.user
                    new_version.statut = VersionDocument.StatutVersion.EN_VIGUEUR
                    # Le statut_diffusion sera 'A_DIFFUSER' par défaut (défini dans le modèle)

                    # 2. Déclassement de l'ancienne version
                    ancienne_version = document.versions.filter(statut=VersionDocument.StatutVersion.EN_VIGUEUR).first()
                    if ancienne_version:
                        ancienne_version.statut = VersionDocument.StatutVersion.REMPLACEE
                        ancienne_version.save()
                    
                    # 3. Sauvegarde de la nouvelle version
                    new_version.save()

                    # 4. Mise à jour de la fiche du document parent
                    document.date_echeance_suivi = new_version.date_mise_en_vigueur + timedelta(days=365)
                    document.statut_suivi = Document.StatutSuivi.A_JOUR
                    document.save()

                    # 5. SUPPRESSION DE LA CRÉATION AUTOMATIQUE D'ACTIONS
                    # La logique qui créait les actions de diffusion ici a été retirée.
                    # Le processus sera maintenant initié manuellement par l'utilisateur
                    # depuis la liste des documents.

                messages.success(request, f"La version {new_version.numero_version} a été enregistrée. Elle est maintenant prête pour la diffusion.")
                # On redirige vers la liste pour qu'il puisse voir le bouton "Diffuser"
                return redirect('documentation:liste-documents')

            except Exception as e:
                messages.error(request, f"Une erreur inattendue est survenue : {e}")
    else:
        form = AddVersionForm()

    context = {
        'form': form,
        'document': document,
        'titre': f"Ajouter une version à {document.reference}"
    }
    return render(request, 'documentation/add_version.html', context)

@login_required
# @permission_required('documentation.add_document', raise_exception=True)
def create_document_view(request):
    """
    Gère le formulaire et la logique pour créer une nouvelle fiche document.
    """
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            document = form.save()
            messages.success(request, f"La fiche document '{document.reference}' a été créée avec succès. Vous pouvez maintenant y ajouter sa première version.")
            # On redirige l'utilisateur directement vers la page de détail pour l'étape suivante
            return redirect('documentation:detail-document', document_id=document.id)
    else:
        form = DocumentForm()

    context = {
        'form': form,
        'titre': "Créer une nouvelle fiche document"
    }
    return render(request, 'documentation/create_document.html', context)