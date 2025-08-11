# Fichier : documentation/views/consultation.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
# --- MODIFICATION DE CETTE LIGNE ---
from ..models import Document, DocumentType, DocumentPriseEnCompte
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
    """
    Affiche la vue de détail d'un document, incluant maintenant l'historique
    des diffusions ET le nouveau journal des prises en compte.
    """
    document = get_object_or_404(Document.objects.select_related(
        'remplace_document', 'document_parent', 'remplace_par'
    ), pk=document_id)

    # --- DÉBUT DE LA LOGIQUE AJOUTÉE ---
    
    # 1. On récupère le paramètre d'URL pour savoir si on doit afficher les agents inactifs.
    # C'est ce qui permettra au bouton "Afficher/Masquer" de fonctionner.
    show_inactive = request.GET.get('show_inactive', 'false').lower() == 'true'

    # 2. On commence la requête de base pour récupérer les prises en compte.
    # On pré-charge les informations de l'agent et de son centre pour optimiser.
    prises_en_compte = DocumentPriseEnCompte.objects.filter(
        document=document
    ).select_related('agent', 'agent__centre').order_by('timestamp')

    # 3. PAR DÉFAUT, on applique le filtre pour ne voir que les agents actifs.
    # Si show_inactive est True, cette ligne est ignorée.
    if not show_inactive:
        prises_en_compte = prises_en_compte.filter(agent__actif=True)

    # 4. On applique le filtre de périmètre pour les utilisateurs locaux.
    # Le middleware GirrexContext a déjà mis 'centre_agent' à notre disposition.
    if hasattr(request, 'centre_agent') and request.centre_agent:
        prises_en_compte = prises_en_compte.filter(agent__centre=request.centre_agent)
        
    # --- FIN DE LA LOGIQUE AJOUTÉE ---

    context = { 
        'document': document, 
        'titre': f"Détail : {document.reference}",
        'prises_en_compte': prises_en_compte,  # On passe la liste (filtrée ou non) au template
        'show_inactive': show_inactive,        # On passe le statut du filtre pour le bouton
    }
    return render(request, 'documentation/detail_document.html', context)