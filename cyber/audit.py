# Fichier : cyber/audit.py (NOUVEAU FICHIER)

from django.utils import timezone
from .models import CyberRisqueHistorique, CyberIncidentHistorique

def log_audit_risque(risque, type_evenement, auteur, details=None):
    """
    Enregistre une entrée dans le journal d'audit permanent d'un CyberRisque.
    """
    CyberRisqueHistorique.objects.create(
        risque=risque,
        type_evenement=type_evenement,
        auteur=auteur,
        details=details or {},
        timestamp=timezone.now() 
    )

def log_audit_incident(incident, type_evenement, auteur, details=None):
    """
    Enregistre une entrée dans le journal d'audit permanent d'un CyberIncident.
    """
    CyberIncidentHistorique.objects.create(
        incident=incident,
        type_evenement=type_evenement,
        auteur=auteur,
        details=details or {},
        timestamp=timezone.now() 
    )