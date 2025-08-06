# Fichier : core/decorators.py (Version Corrigée et Optimisée)

from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib.auth.views import redirect_to_login
from .models import FeuilleTempsVerrou

def effective_permission_required(permission_name, raise_exception=True):
    """
    Décorateur qui vérifie une permission en se basant sur le contexte
    pré-calculé par le GirrexContextMiddleware et disponible dans 'request.effective_perms'.
    Cette version ne recalcule rien, elle est donc beaucoup plus performante.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Le middleware a déjà fait tout le travail de calcul. 
            # On vérifie simplement si la permission est dans le set final.
            if not hasattr(request, 'effective_perms') or permission_name not in request.effective_perms:
                if raise_exception:
                    raise PermissionDenied("Vous n'avez pas la permission requise pour accéder à cette page.")
                
                # Redirige vers la page de login si l'utilisateur n'est pas authentifié
                return redirect_to_login(request.get_full_path())
            
            # Si la permission est trouvée, on exécute la vue normalement.
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def cdq_lock_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur connecté est bien le Chef de Quart (CDQ)
    qui a verrouillé la feuille de temps pour le centre concerné.
    Attend que la vue reçoive un `centre_id` dans ses kwargs.
    (Cette fonction est conservée à l'identique car elle était correcte).
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