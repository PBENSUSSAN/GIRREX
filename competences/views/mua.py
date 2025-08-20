# Fichier : competences/views/mua.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from core.models import Parametre
from ..models import MentionUniteAnnuelle, RegleDeRenouvellement
from .dossier import calculer_statut_socle

@login_required
def dossier_mua_view(request, mua_id):
    """
    Affiche le dossier de suivi/renouvellement pour une MUA spécifique,
    avec une checklist 100% dynamique.
    """
    mua = get_object_or_404(
        MentionUniteAnnuelle.objects.select_related('qualification__brevet__agent', 'qualification__centre'),
        pk=mua_id
    )
    agent = mua.qualification.brevet.agent
    
    checklist = []
    toutes_conditions_remplies = True

    # --- Étape 1 : Vérification du Socle ---
    statut_socle = calculer_statut_socle(agent)
    for nom_check, cle_details, nom_champ_date in [
        ('Aptitude Médicale', 'certificat_medical', 'date_expiration_aptitude'),
        ('Aptitude Linguistique', 'mention_linguistique', 'date_echeance'),
        ('Formation RAF AERO', 'raf_aero', 'date_echeance')
    ]:
        objet = statut_socle['details'][cle_details]
        date_echeance = getattr(objet, nom_champ_date, None)
        est_valide = objet and date_echeance and date_echeance >= timezone.now().date()
        
        check = {
            'nom': nom_check,
            'valide': est_valide,
            'details': f"Expire le {date_echeance.strftime('%d/%m/%Y')}" if est_valide else "Manquant ou expiré"
        }
        checklist.append(check)
        if not est_valide: toutes_conditions_remplies = False

    # --- Étape 2 : Vérification des règles de renouvellement d'heures ---
    
    # Récupération des plafonds (avec une valeur par défaut robuste)
    try:
        plafond_cdq = int(Parametre.objects.get(nom='PLAFOND_HEURES_CDQ').valeur_defaut)
    except (Parametre.DoesNotExist, ValueError):
        plafond_cdq = 20 # Valeur de secours
    
    try:
        plafond_superviseur = int(Parametre.objects.get(nom='PLAFOND_HEURES_SUPERVISEUR').valeur_defaut)
    except (Parametre.DoesNotExist, ValueError):
        plafond_superviseur = 20 # Valeur de secours

    # On applique les plafonds
    heures_cdq_valides = min(mua.heures_en_cdq, plafond_cdq)
    heures_supervision_valides = min(mua.heures_en_supervision, plafond_superviseur)

    # Dictionnaire des heures valides pour les règles
    heures_disponibles = {
        'heures_cam_effectuees': mua.heures_cam_effectuees + heures_cdq_valides + heures_supervision_valides,
        'heures_cag_acs_effectuees': mua.heures_cag_acs_effectuees,
        'heures_cag_aps_effectuees': mua.heures_cag_aps_effectuees,
        'heures_tour_effectuees': mua.heures_tour_effectuees,
    }

    regles = RegleDeRenouvellement.objects.filter(
        centre=mua.qualification.centre,
        type_flux_mua=mua.type_flux
    )

    for regle in regles:
        heures_source_1 = heures_disponibles.get(regle.source_heures_1, 0)
        check_1_valide = heures_source_1 >= regle.seuil_heures_1
        
        check_2_valide = True # Valide par défaut si pas de règle 2
        if regle.source_heures_2 and regle.seuil_heures_2 is not None:
             heures_source_2 = heures_disponibles.get(regle.source_heures_2, 0)
             check_2_valide = heures_source_2 >= regle.seuil_heures_2

        est_valide = check_1_valide and check_2_valide
        details_str = f"{heures_source_1}/{regle.seuil_heures_1}"
        
        check = {
            'nom': regle.nom_regle,
            'valide': est_valide,
            'details': details_str
        }
        checklist.append(check)
        if not est_valide: toutes_conditions_remplies = False

    context = {
        'mua': mua,
        'agent_concerne': agent,
        'titre': f"Dossier de suivi MUA {mua.get_type_flux_display()} pour {agent.trigram}",
        'checklist': checklist,
        'toutes_conditions_remplies': toutes_conditions_remplies,
    }
    return render(request, 'competences/dossier_mua.html', context)