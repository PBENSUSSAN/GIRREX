# Fichier : core/context_processors.py

from django.utils.functional import SimpleLazyObject
from .permissions import has_effective_permission
from .models import FeuilleTempsVerrou
from datetime import date

# ==============================================================================
# PROCESSEUR POUR LES PERMISSIONS EFFECTIVES (CODE EXISTANT CONSERVÉ)
# ==============================================================================

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
        # Nécessaire pour que des constructions comme `{% if 'perm' in perms %}` fonctionnent.
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

# ==============================================================================
# NOUVEAU PROCESSEUR POUR LE CONTEXTE GLOBAL (VERROU, CENTRE, DATE)
# ==============================================================================

def girrex_global_context(request):
    """
    Injecte des variables globales liées à l'état opérationnel 
    (verrou, centre de l'agent, date du jour) dans le contexte de tous les templates.
    Ceci est essentiel pour que la sidebar (base.html) puisse afficher l'état
    du verrouillage en temps réel sur n'importe quelle page.
    """
    context_data = {
        'today': date.today(),
        'verrou_operationnel': None, # On nomme la variable différemment pour éviter tout conflit
        'centre_agent': None,
    }

    # La logique ne s'exécute que pour les utilisateurs connectés ayant un profil Agent.
    # C'est une optimisation pour ne pas faire de requêtes inutiles pour les anonymes.
    if request.user.is_authenticated and hasattr(request.user, 'agent_profile'):
        agent_centre = request.user.agent_profile.centre
        context_data['centre_agent'] = agent_centre
        
        if agent_centre:
            # On cherche le verrou pour le centre de l'agent connecté.
            # 'select_related' optimise la requête en pré-chargeant les données du chef de quart
            # pour éviter une requête supplémentaire lors de l'accès à `verrou.chef_de_quart`.
            verrou = FeuilleTempsVerrou.objects.select_related('chef_de_quart').filter(centre=agent_centre).first()
            context_data['verrou_operationnel'] = verrou
            
    return context_data