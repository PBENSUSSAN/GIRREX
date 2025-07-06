# Fichier : core/permissions.py (NOUVEAU FICHIER)

from datetime import date
from .models import Delegation

def has_effective_permission(user, permission_name):
    """
    Vérifie si un utilisateur a une permission, soit directement,
    soit via une délégation active.
    
    :param user: L'objet User de Django.
    :param permission_name: Le nom de la permission (ex: 'core.view_agent').
    :return: True si l'utilisateur a la permission, False sinon.
    """
    if not user.is_authenticated:
        return False

    # 1. Vérification directe des permissions de l'utilisateur
    if user.has_perm(permission_name):
        return True

    # 2. Vérification via délégation active
    # On vérifie d'abord si l'utilisateur a un profil Agent
    if not hasattr(user, 'agent_profile'):
        return False
        
    today = date.today()
    
    # On cherche toutes les délégations actives où cet utilisateur est le bénéficiaire
    active_delegations = Delegation.objects.filter(
        delegataire=user.agent_profile,
        date_debut__lte=today,
        date_fin__gte=today
    )
    
    # Pour chaque délégation active, on vérifie si l'agent qui délègue a la permission
    for delegation in active_delegations:
        delegant_user = delegation.delegant.user
        if delegant_user and delegant_user.has_perm(permission_name):
            # Dès qu'on trouve la permission via un délégant, on retourne True
            return True
            
    # Si après toutes les vérifications, la permission n'est trouvée nulle part
    return False