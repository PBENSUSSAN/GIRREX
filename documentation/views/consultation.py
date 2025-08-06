# Fichier : documentation/views/consultation.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Document
from ..filters import DocumentFilter

@login_required
def liste_documents_view(request):
    """
    Affiche la liste des documents actifs, en appliquant les filtres
    et en pré-chargeant les versions pour un affichage optimisé.
    """
    base_queryset = Document.objects.filter(
        statut_suivi__in=['A_JOUR', 'EN_REDACTION', 'RENOUVELLEMENT_PLANIFIE', 'PERIME']
    ).prefetch_related('versions')

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