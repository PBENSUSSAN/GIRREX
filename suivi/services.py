# Fichier : suivi/services.py

from .models import Action, HistoriqueAction

def update_parent_progress(action_fille):
    """
    Met à jour l'avancement de l'action parente.
    Bloque la progression à 99% si toutes les sous-tâches sont terminées.
    """
    parent = action_fille.parent
    if not parent:
        return # Pas de parent, rien à faire

    filles = parent.sous_taches.all()
    total_filles = filles.count()
    
    if total_filles == 0:
        return

    filles_validees = filles.filter(statut=Action.StatutAction.VALIDEE).count()
    pourcentage = int((filles_validees / total_filles) * 100)

    # Règle simple et universelle :
    if pourcentage == 100:
        # Si toutes les filles sont terminées, le parent est prêt pour sa propre validation.
        parent.avancement = 99
        parent.statut = Action.StatutAction.A_VALIDER
    else:
        # Sinon, on met simplement à jour le pourcentage.
        parent.avancement = pourcentage
        # Sécurité : si on a rouvert une sous-tâche, on repasse le parent en "En cours".
        if parent.statut == Action.StatutAction.A_VALIDER:
             parent.statut = Action.StatutAction.EN_COURS
    
    parent.save()

def final_close_action_cascade(action, user):
    """
    Passe une action à 100% et propage cette clôture à toutes ses sous-tâches
    qui étaient bloquées à 99% (ou déjà validées).
    """
    # 1. On clôture l'action principale si elle n'est pas déjà à 100%
    if action.avancement < 100:
        ancien_statut_display = action.get_statut_display()
        action.avancement = 100
        action.statut = Action.StatutAction.VALIDEE
        action.save()
        HistoriqueAction.objects.create(
            action=action,
            type_evenement=HistoriqueAction.TypeEvenement.CHANGEMENT_STATUT,
            auteur=user,
            details={'ancien': ancien_statut_display, 'nouveau': "Validée (Clôture SMS)"}
        )

    # 2. On propage la clôture vers le bas (récursivement)
    # On cible les sous-tâches qui ne sont pas encore à 100%
    for sous_tache in action.sous_taches.exclude(avancement=100):
        final_close_action_cascade(sous_tache, user)