# Fichier : core/context_processors.py (VERSION FINALE, COMPLÈTE ET CORRIGÉE)

from django.utils.functional import SimpleLazyObject
from .permissions import has_effective_permission
from .models import FeuilleTempsVerrou, ServiceJournalier, Role
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
# PROCESSEUR GLOBAL (CORRIGÉ POUR LE MENU ET LE TOOLTIP)
# ==============================================================================
def girrex_global_context(request):
    """
    Injecte des variables globales liées à l'état opérationnel et à l'utilisateur
    connecté dans le contexte de tous les templates.
    """
    context_data = {
        'today': date.today(),
        'centre_agent': None,
        'service_du_jour': None,
        'verrou_operationnel': None,
        'user_roles': {},            # CORRIGÉ : Nom de variable aligné sur le template
        'ROLES': Role.RoleName,
        'user_active_roles': [],
        'user_permission_groups': []
    }

    if request.user.is_authenticated and hasattr(request.user, 'agent_profile'):
        agent = request.user.agent_profile
        agent_centre = agent.centre
        context_data['centre_agent'] = agent_centre

        if agent_centre:
            service = ServiceJournalier.objects.filter(
                centre=agent_centre, 
                date_jour=context_data['today']
            ).first()
            context_data['service_du_jour'] = service
            if service and service.statut == ServiceJournalier.StatutJournee.OUVERTE:
                verrou = FeuilleTempsVerrou.objects.select_related('chef_de_quart__user').filter(centre=agent_centre).first()
                context_data['verrou_operationnel'] = verrou
        
        # --- LOGIQUE POUR LES RÔLES ET GROUPES ---
        # 1. Récupérer les objets Rôles actifs pour le tooltip
        active_roles_qs = agent.roles_assignes.filter(date_fin__isnull=True).select_related('role')
        context_data['user_active_roles'] = [ar.role for ar in active_roles_qs]
        
        # 2. Créer le dictionnaire pour les conditions `if` dans le template
        role_names = [role.nom for role in context_data['user_active_roles']]
        context_data['user_roles'] = {role_name: True for role_name in role_names}
        
        # 3. Récupérer les groupes de permissions pour le tooltip
        if agent.user:
             context_data['user_permission_groups'] = agent.user.groups.all().order_by('name')
            
    return context_data