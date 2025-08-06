# Fichier : core/context_processors.py (Version Corrigée et Simplifiée)

from datetime import date
from .middleware import EffectivePermissions # Importe la classe helper

def girrex_global_context(request):
    """
    Expose simplement au template les variables qui ont été pré-calculées 
    par le GirrexContextMiddleware et attachées à l'objet 'request'.
    Cette fonction ne fait plus aucun calcul, elle ne fait que transmettre.
    """
    return {
        # Variables simples qui peuvent être définies ici
        'today': date.today(),
        'ROLES': getattr(request, 'ROLES', {}),

        # On lit toutes les autres variables depuis l'objet 'request'.
        # Le 'getattr' avec une valeur par défaut garantit que ça ne plantera jamais,
        # même si le middleware n'a pas pu définir une variable (ex: utilisateur non connecté).
        'all_user_active_roles': getattr(request, 'all_effective_roles', []),
        'active_agent_role': getattr(request, 'active_agent_role', None),
        'effective_perms': getattr(request, 'effective_perms', EffectivePermissions(set())),
        
        # Flags pour l'affichage des menus
        'is_supervisor_view': getattr(request, 'is_supervisor_view', False),
        'show_operational_view': getattr(request, 'show_operational_view', False),
        'show_sms_menu': getattr(request, 'show_sms_menu', False),
        'show_formation_menu': getattr(request, 'show_formation_menu', False),
        'show_technique_menu': getattr(request, 'show_technique_menu', False),
        'show_security_menu': getattr(request, 'show_security_menu', False),
        
        # Objets de contexte pour la sidebar (logique de verrou, etc.)
        'centre_agent': getattr(request, 'centre_agent', None),
        'service_du_jour': getattr(request, 'service_du_jour', None),
        'verrou_operationnel': getattr(request, 'verrou_operationnel', None),
        
        # Données pour le tooltip de l'utilisateur
        'user_permission_groups': getattr(request, 'user_permission_groups', []),
        'user_active_roles': [ar.role for ar in getattr(request, 'all_effective_roles', [])],
        'user_roles': {ar.role.nom: True for ar in getattr(request, 'all_effective_roles', [])}
    }