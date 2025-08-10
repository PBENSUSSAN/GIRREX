# Fichier : documentation/views/consultation.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import Document, DocumentType
from ..filters import DocumentFilter

@login_required
def liste_documents_view(request):
    """ Affiche la bibliothèque documentaire. """
    base_queryset = Document.objects.filter(
        statut__in=['EN_VIGUEUR', 'REMPLACE', 'EN_REDACTION']
    ).select_related('type_document', 'responsable_suivi')

    if hasattr(request, 'centre_agent') and request.centre_agent:
        base_queryset = base_queryset.filter(
            Q(centres_applicables__isnull=True) |
            Q(centres_applicables=request.centre_agent)
        ).distinct()
    
    document_filter = DocumentFilter(request.GET, queryset=base_queryset, request=request)
    
    context = {
        'filter': document_filter,
        'titre': "Bibliothèque Documentaire"
    }
    return render(request, 'documentation/liste_documents.html', context)


@login_required
def detail_document_view(request, document_id):
    """ Affiche la vue de détail d'un document (sans l'historique des diffusions). """
    document = get_object_or_404(Document.objects.select_related(
        'remplace_document', 'document_parent', 'remplace_par'
    ), pk=document_id)

    context = { 
        'document': document, 
        'titre': f"Détail : {document.reference}" 
    }
    return render(request, 'documentation/detail_document.html', context)