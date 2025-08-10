# Fichier : documentation/views/consultation.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from suivi.models import Action
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
    """ Affiche la vue à 360° d'un document et l'historique de ses diffusions. """
    document = get_object_or_404(Document.objects.select_related(
        'remplace_document', 'document_parent', 'remplace_par'
    ), pk=document_id)

    # On récupère le "type" de l'objet Document
    content_type = ContentType.objects.get_for_model(document)
    
    # On cherche TOUTES les actions (même archivées) qui pointent vers ce document.
    diffusions = Action.archives.filter(
        content_type=content_type, 
        object_id=document.id,
        parent__isnull=True # On ne prend que les actions mères de diffusion
    ).order_by('-id') # On trie par ID pour avoir les plus récentes en premier

    context = { 
        'document': document, 
        'diffusions': diffusions, # On passe la liste des actions au template
        'titre': f"Détail : {document.reference}" 
    }
    return render(request, 'documentation/detail_document.html', context)