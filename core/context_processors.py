# Fichier : core/context_processors.py (VERSION FINALE ET COMPLÈTE)

from django.utils.functional import SimpleLazyObject
from .permissions import has_effective_permission
from .models import FeuilleTempsVerrou, ServiceJournalier
from datetime import date

# ==============================================================================
# PROCESSEUR POUR LES PERMISSIONS EFFECTIVES (INCHANGÉ)
# ==============================================================================

class EffectivePermissions:
    def __init__(self, user): self._user = user
    def __contains__(self, perm_name): return has_effective_permission(self._user, perm_name)
    def __getattr__(self, app_label): return AppPermissions(self._user, app_label)
    def __iter__(self): return iter([])

class AppPermissions:
    def __init__(self, user, app_label): self._user, self._app_label = user, app_label
    def __getattr__(self, perm_name): return has_effective_permission(self._user, f"{self._app_label}.{perm_name}")

def get_effective_perms(user): return EffectivePermissions(user)

def effective_permissions_processor(request):
    return {'effective_perms': SimpleLazyObject(lambda: get_effective_perms(request.user))}

# ==============================================================================
# PROCESSEUR GLOBAL (VERSION CORRIGÉE POUR INCLURE LE VERROU)
# ==============================================================================

def girrex_global_context(request):
    """
    Injecte des variables globales liées à l'état opérationnel dans le contexte.
    """
    context_data = {
        'today': date.today(),
        'verrou_operationnel': None,
        'centre_agent': None,
        'service_du_jour': None, 
    }
    if request.user.is_authenticated and hasattr(request.user, 'agent_profile'):
        agent_centre = request.user.agent_profile.centre
        context_data['centre_agent'] = agent_centre
        if agent_centre:
            # CORRECTION : On s'assure que le verrou est TOUJOURS recherché.
            # C'est cette variable qui manquait et qui faisait disparaître le bouton.
            verrou = FeuilleTempsVerrou.objects.select_related('chef_de_quart').filter(centre=agent_centre).first()
            context_data['verrou_operationnel'] = verrou
            
            # La logique pour le service actif reste la même (elle est correcte)
            service_actif = ServiceJournalier.objects.filter(
                centre=agent_centre, 
                statut=ServiceJournalier.StatutJournee.OUVERTE
            ).order_by('-date_jour').first()

            if not service_actif:
                 service_actif = ServiceJournalier.objects.filter(
                    centre=agent_centre,
                    date_jour=date.today()
                 ).first()
            
            context_data['service_du_jour'] = service_actif
            
    return context_data