# Fichier : qs/audit.py

from django.utils import timezone
from .models import HistoriqueFNE

def log_audit_fne(fne, type_evenement, auteur, details=None):
    """
    Fonction centralisée pour enregistrer une entrée dans le journal d'audit
    permanent d'une FNE.
    
    Args:
        fne (FNE): L'instance de la FNE concernée.
        type_evenement (HistoriqueFNE.TypeEvenement): Le type d'événement à enregistrer.
        auteur (User): L'utilisateur qui a déclenché l'événement.
        details (dict, optional): Un dictionnaire de détails contextuels. Defaults to None.
    """
    # La fonction se charge de créer l'entrée dans le journal avec un timestamp actuel.
    # C'est simple, propre et réutilisable.
    HistoriqueFNE.objects.create(
        fne=fne,
        type_evenement=type_evenement,
        auteur=auteur,
        details=details or {},
        timestamp=timezone.now() 
    )