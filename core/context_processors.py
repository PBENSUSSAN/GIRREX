# Fichier : core/context_processors.py (Version Finale Corrigée pour les Rôles Cumulards)

from django.utils.functional import SimpleLazyObject
from .permissions import has_effective_permission
from .models import FeuilleTempsVerrou, ServiceJournalier, Role, AgentRole, Centre
from datetime import date

# ... (les classes de permissions ne changent pas) ...
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


def girrex_global_context(request):
    """
    Injecte toutes les variables globales et les flags de décision pour l'affichage des menus.
    """
    context_data = {
        'today': date.today(),
        'centre_agent': None,
        'service_du_jour': None,
        'verrou_operationnel': None,
        'user_roles': {},
        'ROLES': Role.RoleName,
        'user_active_roles': [],
        'user_permission_groups': [],
        'all_user_active_roles': [],
        'active_agent_role': None,
        
        # --- FLAGS DE DÉCISION POUR LE TEMPLATE ---
        'is_supervisor_view': False,
        'show_operational_view': False,
        'show_sms_menu': False,
        'show_formation_menu': False,
        'show_technique_menu': False,
        'show_security_menu': False,
    }

    if request.user.is_authenticated and hasattr(request.user, 'agent_profile'):
        agent = request.user.agent_profile
        
        # --- LOGIQUE DE DÉTERMINATION DU CONTEXTE ---
        all_active_roles = AgentRole.objects.filter(
            agent=agent, date_fin__isnull=True
        ).select_related('role', 'centre').order_by('role__nom')
        context_data['all_user_active_roles'] = all_active_roles

        selected_agent_role_id = request.session.get('selected_agent_role_id')
        active_agent_role = all_active_roles.filter(pk=selected_agent_role_id).first()

        if not active_agent_role and all_active_roles.exists():
            active_agent_role = all_active_roles.first()
            request.session['selected_agent_role_id'] = active_agent_role.id
        
        context_data['active_agent_role'] = active_agent_role
        
        active_centre = active_agent_role.centre if active_agent_role else agent.centre
        context_data['centre_agent'] = active_centre

        if active_centre:
            service = ServiceJournalier.objects.filter(centre=active_centre, date_jour=context_data['today']).first()
            context_data['service_du_jour'] = service
            if service and service.statut == ServiceJournalier.StatutJournee.OUVERTE:
                verrou = FeuilleTempsVerrou.objects.select_related('chef_de_quart__user').filter(centre=active_centre).first()
                context_data['verrou_operationnel'] = verrou
        
        # --- LOGIQUE GLOBALE DES RÔLES (pour le tooltip) ---
        active_roles_qs = agent.roles_assignes.filter(date_fin__isnull=True).select_related('role')
        context_data['user_active_roles'] = [ar.role for ar in active_roles_qs]
        role_names = [role.nom for role in context_data['user_active_roles']]
        context_data['user_roles'] = {role_name: True for role_name in role_names}
        if agent.user:
             context_data['user_permission_groups'] = agent.user.groups.all().order_by('name')

        # ==============================================================================
        # DÉCISION FINALE PRISE EN PYTHON POUR TOUS LES MENUS
        # ==============================================================================
        if active_agent_role:
            role_nom = active_agent_role.role.nom
            
            # 1. Vue Supervision ?
            if role_nom in [Role.RoleName.CHEF_DE_DIVISION, Role.RoleName.ADJOINT_CHEF_DE_DIVISION]:
                context_data['is_supervisor_view'] = True

            # 2. Vue Opérationnelle ?
            roles_ops = [Role.RoleName.CONTROLEUR, Role.RoleName.CHEF_DE_QUART, Role.RoleName.CHEF_DE_CENTRE, Role.RoleName.ADJOINT_CHEF_DE_CENTRE, Role.RoleName.COORDONATEUR]
            if role_nom in roles_ops:
                context_data['show_operational_view'] = True

            # 3. Menus de domaine ? (Les superviseurs et chefs de centre voient tout)
            super_roles = [Role.RoleName.CHEF_DE_DIVISION, Role.RoleName.ADJOINT_CHEF_DE_DIVISION, Role.RoleName.CHEF_DE_CENTRE]
            
            if role_nom in super_roles or role_nom in [Role.RoleName.ADJOINT_CONFORMITE, Role.RoleName.SMS_LOCAL, Role.RoleName.RESPONSABLE_SMS]:
                context_data['show_sms_menu'] = True
            
            if role_nom in super_roles or role_nom in [Role.RoleName.FORM_LOCAL, Role.RoleName.ADJOINT_FORM]:
                context_data['show_formation_menu'] = True

            if role_nom in super_roles or role_nom in [Role.RoleName.ES_LOCAL, Role.RoleName.ADJOINT_ES]:
                context_data['show_technique_menu'] = True

            if role_nom in super_roles or role_nom in [Role.RoleName.QS_LOCAL, Role.RoleName.ADJOINT_QS]:
                context_data['show_security_menu'] = True
            
    return context_data