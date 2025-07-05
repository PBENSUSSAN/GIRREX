# Fichier : core/context_processors.py

from .models import AgentRole

def user_roles_processor(request):
    """
    Ce processeur de contexte récupère les rôles de l'utilisateur actuellement connecté
    et les rend disponibles dans tous les templates sous la variable 'user_roles'.
    """
    
    # On vérifie d'abord si un utilisateur est authentifié.
    # Sinon, il est inutile de faire une requête à la base de données.
    if not request.user.is_authenticated:
        return {} # On retourne un dictionnaire vide, aucune variable n'est ajoutée.

    try:
        # On utilise la relation inverse pour trouver les rôles.
        # On part de l'utilisateur connecté (request.user), on va à son profil agent (via agent__user)
        # et on récupère tous les objets AgentRole qui lui sont liés.
        roles_obj = AgentRole.objects.filter(agent__user=request.user)
        
        # On transforme la liste d'objets 'AgentRole' en une simple liste de chaînes de caractères (les noms des rôles).
        # C'est plus facile à utiliser dans les templates. Ex: ['Admin', 'Chef de Quart']
        user_roles_list = [agent_role.role.nom for agent_role in roles_obj]

    except Exception:
        # Si une erreur se produit (par exemple, l'utilisateur n'a pas de profil Agent lié),
        # on s'assure de ne pas faire planter l'application et on retourne une liste vide.
        user_roles_list = []
        
    # Le dictionnaire retourné est ajouté au contexte global.
    # La clé 'user_roles' devient le nom de la variable dans le template.
    return {
        'user_roles': user_roles_list
    }