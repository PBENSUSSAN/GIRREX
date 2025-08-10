# Fichier : documentation/views/gestion.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Document
from ..forms import CreateDocumentForm, UpdateDocumentForm

@login_required
#@permission_required('documentation.add_document', raise_exception=True)
def create_document_view(request):
    """ Gère la création d'une nouvelle fiche document. """
    if request.method == 'POST':
        form = CreateDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # L'appel à form.save() gère à la fois l'objet principal
            # et les relations ManyToMany (comme 'centres_applicables').
            document = form.save()
            
            # La ligne form.save_m2m() est inutile et a été supprimée.
            
            messages.success(request, f"Le document '{document.reference}' a été créé.")
            return redirect('documentation:detail-document', document_id=document.id)
    else:
        form = CreateDocumentForm()

    context = { 'form': form, 'titre': "Créer une Fiche Document" }
    return render(request, 'documentation/create_document.html', context)


@login_required
#@permission_required('documentation.change_document', raise_exception=True)
def modifier_document_view(request, document_id):
    """ Gère la modification d'une fiche document existante. """
    document = get_object_or_404(Document, pk=document_id)
    if request.method == 'POST':
        form = UpdateDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            # De même ici, form.save() gère tout.
            form.save()
            
            # La ligne form.save_m2m() est inutile et a été supprimée.

            messages.success(request, f"Le document '{document.reference}' a été mis à jour.")
            return redirect('documentation:detail-document', document_id=document.id)
    else:
        form = UpdateDocumentForm(instance=document)

    context = { 'form': form, 'document': document, 'titre': f"Modifier : {document.reference}" }
    # On réutilise le template de création pour la modification
    return render(request, 'documentation/create_document.html', context)