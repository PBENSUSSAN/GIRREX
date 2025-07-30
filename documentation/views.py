# Fichier : documentation/views.py (Version complète avec la fonctionnalité d'ajout de version)

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
from .forms import AddVersionForm
from core.models import AgentRole  # Important pour trouver le responsable local
from suivi.models import Action     # Important pour créer la tâche de diffusion
from .filters import DocumentFilter

# ==============================================================================
# Vues de consultation de la bibliothèque
# ==============================================================================

@login_required
def liste_documents_view(request):
    """
    Affiche la liste des documents actifs, en appliquant les filtres
    fournis par l'utilisateur via django-filter.
    """
    # On prend la même base de documents qu'avant
    base_queryset = Document.objects.filter(statut_suivi__in=['A_JOUR', 'EN_REDACTION', 'RENOUVELLEMENT_PLANIFIE', 'PERIME'])
    
    # On instancie notre classe de filtre avec les données GET de la requête et le queryset de base
    document_filter = DocumentFilter(request.GET, queryset=base_queryset)
    
    context = {
        # On passe l'objet filtre complet au template
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
# Vue pour l'ajout d'une nouvelle version (NOUVEAUTÉ)
# ==============================================================================

@login_required
# @permission_required('documentation.add_versiondocument', raise_exception=True) # On activera la permission plus tard
def add_version_view(request, document_id):
    """ Gère le formulaire et la logique pour ajouter une nouvelle version à un document. """
    document = get_object_or_404(Document, pk=document_id)
    
    if request.method == 'POST':
        # On passe request.FILES pour gérer l'upload du fichier
        form = AddVersionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Une transaction atomique garantit que toutes les opérations
                # réussissent, ou qu'aucune n'est appliquée en cas d'erreur.
                with transaction.atomic():
                    # 1. On prépare la nouvelle version sans la sauvegarder en base
                    new_version = form.save(commit=False)
                    new_version.document = document
                    new_version.enregistre_par = request.user
                    new_version.statut = VersionDocument.StatutVersion.EN_VIGUEUR

                    # 2. On trouve l'ancienne version "En Vigueur" et on la déclasse
                    ancienne_version = document.versions.filter(statut=VersionDocument.StatutVersion.EN_VIGUEUR).first()
                    if ancienne_version:
                        ancienne_version.statut = VersionDocument.StatutVersion.REMPLACEE
                        ancienne_version.save()
                    
                    # 3. On sauvegarde la nouvelle version en base de données
                    new_version.save()

                    # 4. On met à jour la fiche du document parent
                    document.date_echeance_suivi = new_version.date_mise_en_vigueur + timedelta(days=365)
                    document.statut_suivi = Document.StatutSuivi.A_JOUR
                    document.save()

                    # 5. On crée les actions de diffusion pour les responsables locaux
                    centres = document.centres_applicables.all()
                    for centre in centres:
                        # On cherche le responsable documentaire du centre
                        responsable_local_role = AgentRole.objects.filter(
                            centre=centre, 
                            role__nom="Responsable Documentaire Local",
                            date_fin__isnull=True  # On s'assure que l'attribution est active
                        ).first()

                        if responsable_local_role:
                            Action.objects.create(
                                titre=f"Diffuser la v{new_version.numero_version} du document '{document.reference}'",
                                responsable=responsable_local_role.agent,
                                echeance=timezone.now().date() + timedelta(days=14),
                                objet_source=new_version # Lien générique vers la nouvelle version
                            )

                messages.success(request, f"La version {new_version.numero_version} a été enregistrée avec succès. Les actions de diffusion ont été créées.")
                return redirect('documentation:detail-document', document_id=document.id)

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