# Fichier : core/context_processors.py (NOUVEAU FICHIER)

from django.utils.functional import SimpleLazyObject
from .permissions import has_effective_permission

class EffectivePermissions:
    """
    Un objet qui imite le `perms` de Django mais utilise notre logique de vérification.
    """
    def __init__(self, user):
        self._user = user

    def __contains__(self, perm_name):
        return has_effective_permission(self._user, perm_name)

    def __getattr__(self, app_label):
        return AppPermissions(self._user, app_label)

    def __iter__(self):
        return iter([])

class AppPermissions:
    """Représente les permissions pour une application."""
    def __init__(self, user, app_label):
        self._user = user
        self._app_label = app_label

    def __getattr__(self, perm_name):
        perm_path = f"{self._app_label}.{perm_name}"
        return has_effective_permission(self._user, perm_path)

def get_effective_perms(user):
    return EffectivePermissions(user)

def effective_permissions_processor(request):
    """
    Ajoute `effective_perms` au contexte de tous les templates.
    """
    return {
        'effective_perms': SimpleLazyObject(lambda: get_effective_perms(request.user))
    }