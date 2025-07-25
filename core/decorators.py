# Fichier : core/decorators.py

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .permissions import has_effective_permission
from .models import FeuilleTempsVerrou

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

def cdq_lock_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur connecté est bien le Chef de Quart (CDQ)
    qui a verrouillé la feuille de temps pour le centre concerné.
    Attend que la vue reçoive un `centre_id` dans ses kwargs.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        centre_id = kwargs.get('centre_id')
        if not centre_id:
            raise ValueError("Le décorateur @cdq_lock_required requiert un 'centre_id' dans les paramètres de l'URL.")

        if not hasattr(request.user, 'agent_profile'):
            raise PermissionDenied("Accès refusé : votre compte utilisateur n'est pas lié à un profil agent.")

        try:
            verrou = FeuilleTempsVerrou.objects.get(centre_id=centre_id)
            if verrou.chef_de_quart != request.user.agent_profile:
                raise PermissionDenied(f"Accès refusé : le service est actuellement pris par {verrou.chef_de_quart}.")

        except FeuilleTempsVerrou.DoesNotExist:
            raise PermissionDenied("Accès refusé : le service doit être pris (verrouillage) pour effectuer cette action.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view