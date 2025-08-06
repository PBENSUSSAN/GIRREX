# Fichier : documentation/views/gestion.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from ..models import Document, VersionDocument
from ..forms import AddVersionForm, DocumentForm

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
                    new_version = form.save(commit=False)
                    new_version.document = document
                    new_version.enregistre_par = request.user
                    new_version.statut = VersionDocument.StatutVersion.EN_VIGUEUR
                    
                    ancienne_version = document.versions.filter(statut=VersionDocument.StatutVersion.EN_VIGUEUR).first()
                    if ancienne_version:
                        ancienne_version.statut = VersionDocument.StatutVersion.REMPLACEE
                        ancienne_version.save()
                    
                    new_version.save()

                    document.date_echeance_suivi = new_version.date_mise_en_vigueur + timedelta(days=365)
                    document.statut_suivi = Document.StatutSuivi.A_JOUR
                    document.save()

                messages.success(request, f"La version {new_version.numero_version} a été enregistrée. Elle est maintenant prête pour la diffusion.")
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
            return redirect('documentation:detail-document', document_id=document.id)
    else:
        form = DocumentForm()

    context = {
        'form': form,
        'titre': "Créer une nouvelle fiche document"
    }
    return render(request, 'documentation/create_document.html', context)