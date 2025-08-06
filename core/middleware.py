# Fichier : core/middleware.py (Version Finale et Complète)

from datetime import date
from .models import AgentRole, Delegation, Role, Centre, ServiceJournalier, FeuilleTempsVerrou
from django.contrib.auth.models import Group

# ==============================================================================
# CLASSES HELPER POUR LA GESTION DES PERMISSIONS
# ==============================================================================
class EffectivePermissions:
    """
    Objet pratique pour vérifier les permissions dans les templates
    (ex: {% if effective_perms.core.view_feuilletemps %}).
    """
    def __init__(self, permission_set):
        self.permission_set = permission_set or set()
    def __contains__(self, perm_name):
        return perm_name in self.permission_set
    def __getattr__(self, app_label):
        return AppPermissions(self, app_label)

class AppPermissions:
    def __init__(self, effective_perms, app_label):
        self._effective_perms = effective_perms
        self._app_label = app_label
    def __getattr__(self, perm_name):
        return f"{self._app_label}.{perm_name}" in self._effective_perms

# ==============================================================================
# MIDDLEWARE PRINCIPAL DE L'APPLICATION
# ==============================================================================
class GirrexContextMiddleware:
    """
    Middleware central qui calcule TOUT le contexte nécessaire pour l'utilisateur
    connecté (rôles, permissions, drapeaux d'affichage, etc.) et l'attache
    à l'objet 'request' pour une utilisation ultérieure dans les vues et les templates.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Initialisation par défaut de tous les attributs sur la requête
        self._initialize_request_attributes(request)

        if request.user.is_authenticated and hasattr(request.user, 'agent_profile'):
            self._process_authenticated_user(request)

        response = self.get_response(request)
        return response

    def _initialize_request_attributes(self, request):
        request.all_effective_roles = []
        request.active_agent_role = None
        request.effective_perms = EffectivePermissions(set())
        request.is_supervisor_view = False
        request.show_operational_view = False
        request.show_sms_menu = False
        request.show_formation_menu = False
        request.show_technique_menu = False
        request.show_security_menu = False
        request.centre_agent = None
        request.service_du_jour = None
        request.verrou_operationnel = None
        request.user_permission_groups = []
        request.ROLES = Role.RoleName # Expose les noms de rôles

    def _process_authenticated_user(self, request):
        agent = request.user.agent_profile
        today = date.today()

        # 1. RÉCUPÉRATION DES RÔLES EFFECTIFS (PROPRES + DÉLÉGUÉS)
        roles_propres = list(AgentRole.objects.filter(agent=agent, date_fin__isnull=True).select_related('role', 'centre'))
        delegations_recues = Delegation.objects.filter(
            delegataire=agent, date_debut__lte=today, date_fin__gte=today, agent_role_delegue__isnull=False
        ).select_related('agent_role_delegue__role', 'agent_role_delegue__centre')
        
        roles_delegues = [d.agent_role_delegue for d in delegations_recues]
        all_effective_roles = sorted(roles_propres + roles_delegues, key=lambda r: r.role.nom)
        request.all_effective_roles = all_effective_roles

        # 2. CALCUL DES PERMISSIONS EFFECTIVES CUMULATIVES
        final_permission_set = set(request.user.get_user_permissions())
        group_ids = set(g.id for r in all_effective_roles for g in r.role.groups.all())
        group_ids.update(agent.user.groups.values_list('id', flat=True))
        
        permissions_from_groups = Group.objects.filter(pk__in=group_ids).values_list('permissions__content_type__app_label', 'permissions__codename')
        final_permission_set.update(f"{app_label}.{codename}" for app_label, codename in permissions_from_groups)
        
        request.effective_perms = EffectivePermissions(final_permission_set)

        # 3. DÉTERMINATION DU CONTEXTE ACTIF (RÔLE SÉLECTIONNÉ)
        selected_agent_role_id = request.session.get('selected_agent_role_id')
        active_agent_role = next((role for role in all_effective_roles if role.id == selected_agent_role_id), None)
        
        if not active_agent_role and all_effective_roles:
            active_agent_role = all_effective_roles[0]
            request.session['selected_agent_role_id'] = active_agent_role.id
        request.active_agent_role = active_agent_role
        
        # 4. DÉTERMINATION DU CONTEXTE OPÉRATIONNEL (CENTRE, SERVICE, VERROU)
        active_centre = active_agent_role.centre if active_agent_role else agent.centre
        request.centre_agent = active_centre

        if active_centre:
            request.service_du_jour = ServiceJournalier.objects.filter(centre=active_centre, date_jour=today).first()
            if request.service_du_jour and request.service_du_jour.statut == ServiceJournalier.StatutJournee.OUVERTE:
                request.verrou_operationnel = FeuilleTempsVerrou.objects.select_related('chef_de_quart__user').filter(centre=active_centre).first()

        # 5. DÉCISION FINALE POUR L'AFFICHAGE DES BLOCS DE MENUS
        if active_agent_role:
            role_nom = active_agent_role.role.nom
            super_roles = [Role.RoleName.CHEF_DE_DIVISION, Role.RoleName.ADJOINT_CHEF_DE_DIVISION]
            manager_roles = [Role.RoleName.CHEF_DE_CENTRE, Role.RoleName.ADJOINT_CHEF_DE_CENTRE]
            roles_ops = [Role.RoleName.CONTROLEUR, Role.RoleName.CHEF_DE_QUART, Role.RoleName.COORDONATEUR] + manager_roles

            if role_nom in super_roles: request.is_supervisor_view = True
            if role_nom in roles_ops: request.show_operational_view = True
            
            if role_nom in super_roles or role_nom in manager_roles or role_nom in [Role.RoleName.ADJOINT_CONFORMITE, Role.RoleName.SMS_LOCAL, Role.RoleName.RESPONSABLE_SMS]: request.show_sms_menu = True
            if role_nom in super_roles or role_nom in manager_roles or role_nom in [Role.RoleName.ADJOINT_FORM, Role.RoleName.FORM_LOCAL]: request.show_formation_menu = True
            if role_nom in super_roles or role_nom in manager_roles or role_nom in [Role.RoleName.ES_LOCAL, Role.RoleName.ADJOINT_ES]: request.show_technique_menu = True
            if role_nom in super_roles or role_nom in manager_roles or role_nom in [Role.RoleName.QS_LOCAL, Role.RoleName.ADJOINT_QS]: request.show_security_menu = True
        
        # 6. LOGIQUE POUR LE TOOLTIP D'INFORMATIONS UTILISATEUR
        request.user_permission_groups = Group.objects.filter(pk__in=group_ids).order_by('name')

# ==============================================================================
# MIDDLEWARE NO-CACHE
# ==============================================================================
class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response