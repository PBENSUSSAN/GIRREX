# Fichier : core/services.py (VERSION FINALE, COMPLÈTE ET ROBUSTE)

from datetime import datetime, timedelta
from .models import FeuilleTempsEntree, Agent

def _calculer_duree_travail(pointage):
    """
    Fonction utilitaire interne pour calculer la durée de travail d'un pointage,
    en gérant correctement les vacations de nuit.
    Renvoie un objet timedelta et les datetimes de début/fin.
    """
    if not pointage or not pointage.heure_arrivee or not pointage.heure_depart:
        return timedelta(0), None, None

    arrivee_dt = datetime.combine(pointage.date_jour, pointage.heure_arrivee)
    
    if pointage.heure_depart < pointage.heure_arrivee:
        # Vacation de nuit
        depart_dt = datetime.combine(pointage.date_jour + timedelta(days=1), pointage.heure_depart)
    else:
        # Vacation de jour
        depart_dt = datetime.combine(pointage.date_jour, pointage.heure_depart)
        
    return depart_dt - arrivee_dt, arrivee_dt, depart_dt


def verifier_regles_horaires(agent, date_jour, heure_arrivee, heure_depart, est_j_plus_1=False):
    """
    Vérifie les horaires saisis en tenant compte du paramètre 'est_j_plus_1'.
    Renvoie une liste de messages d'erreur. Une liste vide signifie que tout est OK.
    """
    if not heure_arrivee or not heure_depart:
        return []

    erreurs = []

    # --- Étape 1 : Valider la cohérence de la saisie actuelle et calculer sa durée ---
    
    arrivee_dt_actuel = datetime.combine(date_jour, heure_arrivee)
    depart_dt_actuel = None

    if heure_depart < heure_arrivee:
        if est_j_plus_1:
            # L'utilisateur a confirmé la vacation de nuit
            depart_dt_actuel = datetime.combine(date_jour + timedelta(days=1), heure_depart)
        else:
            # Erreur de saisie non confirmée
            erreurs.append("L'heure de départ ne peut pas être antérieure à l'heure d'arrivée.")
            return erreurs
    else:
        # Vacation de jour normale
        depart_dt_actuel = datetime.combine(date_jour, heure_depart)

    duree_actuelle = depart_dt_actuel - arrivee_dt_actuel

    # Règle "garde-fou" : durée de travail invraisemblable
    if duree_actuelle.total_seconds() > 14 * 3600:
        erreurs.append("Durée de travail supérieure à 14h, veuillez vérifier la saisie.")
        return erreurs

    # Règle 1: Durée Max Journalière (> 10h)
    if duree_actuelle.total_seconds() > 10 * 3600:
        duree_str = f"{int(duree_actuelle.total_seconds() // 3600)}h{str(int((duree_actuelle.total_seconds() // 60) % 60)).zfill(2)}"
        erreurs.append(f"Durée de travail dépassée ({duree_str} / 10h00)")

    # --- Étape 2 : Récupérer et analyser l'historique ---

    historique_pointages = FeuilleTempsEntree.objects.filter(
        agent=agent,
        date_jour__range=(date_jour - timedelta(days=7), date_jour - timedelta(days=1))
    ).order_by('-date_jour')

    pointage_veille = historique_pointages.first()

    # Règle 4: Repos Minimum Quotidien (< 11h)
    if pointage_veille:
        _, _, depart_veille_dt = _calculer_duree_travail(pointage_veille)
        if depart_veille_dt: # S'assurer que la veille a bien une heure de départ
            repos_entre_jours = arrivee_dt_actuel - depart_veille_dt
            if repos_entre_jours.total_seconds() < 11 * 3600:
                repos_secondes = repos_entre_jours.total_seconds()
                repos_str = f"{int(repos_secondes // 3600)}h{str(int((repos_secondes // 60) % 60)).zfill(2)}"
                erreurs.append(f"Repos quotidien insuffisant ({repos_str} / 11h00)")

    # Règle 2: Plafond Haut Consécutif (> 9h sur 2 jours)
    if duree_actuelle.total_seconds() > 9 * 3600 and pointage_veille:
        duree_veille, _, _ = _calculer_duree_travail(pointage_veille)
        if duree_veille.total_seconds() > 9 * 3600:
            erreurs.append("Dépassement de 9h sur 2 jours consécutifs")

    # --- Étape 3 : Calculs sur 7 jours flottants ---
    
    total_duree_hebdo = duree_actuelle
    jours_travailles_hebdo = 1 if duree_actuelle.total_seconds() > 0 else 0

    # On parcourt l'historique des 6 jours précédents
    for p in historique_pointages.filter(date_jour__gte=date_jour - timedelta(days=6)):
        duree_passee, _, _ = _calculer_duree_travail(p)
        if duree_passee.total_seconds() > 0:
            total_duree_hebdo += duree_passee
            jours_travailles_hebdo += 1
            
    # Règle 3: Durée Max Hebdomadaire Flottante (> 42h)
    total_secondes_hebdo = total_duree_hebdo.total_seconds()
    if total_secondes_hebdo > 42 * 3600:
        total_str = f"{int(total_secondes_hebdo // 3600)}h{str(int((total_secondes_hebdo // 60) % 60)).zfill(2)}"
        erreurs.append(f"Durée hebdo dépassée ({total_str} / 42h00)")

    # Règle 5: Repos Minimum Hebdomadaire Flottant
    if jours_travailles_hebdo >= 7:
        erreurs.append("Pas de jour de repos sur les 7 derniers jours")

    return erreurs