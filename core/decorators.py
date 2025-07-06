# Fichier : core/decorators.py (NOUVEAU FICHIER)

from django.core.exceptions import PermissionDenied
from functools import wraps
from .permissions import has_effective_permission

def effective_permission_required(permission_name, raise_exception=True):
    """
    Décorateur qui vérifie une permission en tenant compte des délégations.
    Si l'utilisateur n'a pas la permission, lève une PermissionDenied.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not has_effective_permission(request.user, permission_name):
                if raise_exception:
                    raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator