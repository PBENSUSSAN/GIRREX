# Fichier : documentation/tasks.py
from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

# On importe les modèles depuis une autre app, c'est une bonne pratique
from suivi.models import Action

@shared_task
def creer_action_pour_etape_signature(etape_signature_id):
    
    # On doit ré-importer les modèles à l'intérieur de la tâche
    # c'est une bonne pratique pour éviter les imports circulaires.
    from .models import EtapeSignature

    try:
        etape = EtapeSignature.objects.get(pk=etape_signature_id)
        document_ref = etape.version_document.document.reference
        version_num = etape.version_document.numero_version

        # On vérifie si une action n'existe pas déjà pour cette étape
        content_type = ContentType.objects.get_for_model(etape)
        if Action.objects.filter(content_type=content_type, object_id=etape.id).exists():
            return f"Une action existe déjà pour l'étape {etape.id}. Aucune action créée."

        # Création de l'action de suivi
        nouvelle_action = Action.objects.create(
            titre=f"Signer le document {document_ref} - Version {version_num}",
            responsable=etape.signataire,
            # Le validateur n'est pas nécessaire ici, la validation est la signature elle-même
            # L'échéance pourrait être calculée, pour l'instant mettons J+7
            echeance=(timezone.now() + timedelta(days=7)).date(),
            # Lien générique vers l'étape de signature
            objet_source=etape
        )
        return f"Action {nouvelle_action.numero_action} créée pour l'étape de signature {etape.id}."

    except EtapeSignature.DoesNotExist:
        return f"Erreur: EtapeSignature avec l'ID {etape_signature_id} non trouvée."