# Fichier : competences/services.py

from django.utils import timezone
from calendar import monthrange
from datetime import date, timedelta
from collections import defaultdict

from core.models import Parametre, CertificatMed
from activites.models import SaisieActivite
from .models import MentionUniteAnnuelle, MentionLinguistique, SuiviFormationReglementaire, RegleDeRenouvellement

def get_mua_dossier_context(mua):
    """
    Service principal qui prend une MUA et retourne tout le contexte calculé
    nécessaire pour afficher son dossier de renouvellement.
    """
    agent = mua.qualification.brevet.agent
    centre = mua.qualification.centre
    
    # --- 1. Calcul du Socle de Validité ---
    socle_context = calculer_statut_socle(agent)
    checklist_socle = socle_context['checklist']
    socle_est_valide = socle_context['est_valide']
        
    # --- 2. Génération des périodes mensuelles ---
    periods = []
    current_date = mua.date_debut_cycle
    while current_date <= mua.date_fin_cycle:
        end_of_month = date(current_date.year, current_date.month, monthrange(current_date.year, current_date.month)[1])
        period_end = min(end_of_month, mua.date_fin_cycle)
        period_start = max(current_date, mua.date_debut_cycle)
        
        if period_start.day == 1 and period_end.day == monthrange(period_end.year, period_end.month)[1]:
            label = period_start.strftime("%B %Y")
        else:
            label = f"{period_start.strftime('%d/%m')} - {period_end.strftime('%d/%m/%Y')}"
            
        periods.append({'label': label, 'start': period_start, 'end': period_end})
        current_date = (end_of_month + timedelta(days=1))

    # --- 3. Agrégation des heures pour chaque période ---
    activites = SaisieActivite.objects.filter(agent=agent, vol__date_vol__gte=mua.date_debut_cycle, vol__date_vol__lte=mua.date_fin_cycle, vol__centre=centre).select_related('vol')
    
    monthly_breakdown = []
    for period in periods:
        period_activities = [a for a in activites if period['start'] <= a.vol.date_vol <= period['end']]
        
        heures_period = defaultdict(lambda: defaultdict(float))
        for activite in period_activities:
            flux_key = activite.vol.flux.lower()
            role_key = activite.role.lower()
            heures_period[flux_key][role_key] += activite.vol.duree
            
        monthly_breakdown.append({'label': period['label'], 'heures': heures_period})

    # --- 4. Calcul des totaux bruts ---
    heures_brutes_totales = defaultdict(float)
    for month_data in monthly_breakdown:
        for flux, roles in month_data['heures'].items():
            for role, hours in roles.items():
                if role in ['controleur', 'stagiaire']:
                    heures_brutes_totales[flux] += hours
                else:
                    heures_brutes_totales[role] += hours
    
    # --- 5. Calcul des Barres de Progression ---
    barres_progression = []
    heures_sont_valides = True
    regle = RegleDeRenouvellement.objects.filter(centres=centre).first()

    if regle:
        try:
            plafond_roles = int(Parametre.objects.get(nom='PLAFOND_HEURES_ROLES_SPECIFIQUES').valeur_defaut)
        except (Parametre.DoesNotExist, ValueError):
            plafond_roles = 20
            
        heures_roles_brutes = heures_brutes_totales['isp'] + heures_brutes_totales['cdq'] + heures_brutes_totales['superviseur']
        heures_roles_valides = min(heures_roles_brutes, plafond_roles)
        
        heures_actives_cam = heures_brutes_totales['cam']
        heures_actives_cag = heures_brutes_totales['cag_acs'] + heures_brutes_totales['cag_aps'] + heures_brutes_totales['tour']
        
        total_cam = heures_actives_cam + heures_roles_valides
        total_cag = heures_actives_cag
        total_general = total_cam + total_cag
        
        objectifs = {
            'Total Activité': (total_general, regle.seuil_heures_total),
            'Spécifique CAM': (total_cam, regle.seuil_heures_cam),
            'Spécifique CAG ACS': (heures_brutes_totales['cag_acs'], regle.seuil_heures_cag_acs),
            'Spécifique CAG APS': (heures_brutes_totales['cag_aps'], regle.seuil_heures_cag_aps),
            'Spécifique TOUR': (heures_brutes_totales['tour'], regle.seuil_heures_tour),
        }
        for nom, (effectue, requis) in objectifs.items():
            if requis > 0:
                est_valide = effectue >= requis
                barre = {'nom': nom, 'effectue': effectue, 'requis': requis, 'pourcentage': min(int((effectue / requis) * 100), 100), 'valide': est_valide, 'est_objectif': True}
                barres_progression.append(barre)
                if not est_valide: heures_sont_valides = False
        
        roles_plafonnés = {
            'Heures en CDQ': (heures_brutes_totales['cdq'], plafond_roles),
            'Heures en Supervision': (heures_brutes_totales['superviseur'], plafond_roles),
            'Heures en ISP': (heures_brutes_totales['isp'], plafond_roles),
        }
        for nom, (effectue, requis) in roles_plafonnés.items():
            if effectue > 0 or requis > 0:
                barre = {'nom': nom, 'effectue': effectue, 'requis': requis, 'pourcentage': min(int((effectue / requis) * 100), 100), 'valide': True, 'est_objectif': False}
                barres_progression.append(barre)
                
    # --- 6. Retourner le dictionnaire de contexte unifié ---
    return {
        'checklist_socle': checklist_socle,
        'barres_progression': barres_progression,
        'toutes_conditions_remplies': socle_est_valide and heures_sont_valides,
        'monthly_breakdown': monthly_breakdown,
        'heures_brutes_totales': heures_brutes_totales,
    }

# ==========================================================
#                      NOUVELLE SECTION
# ==========================================================

def calculer_statut_socle(agent):
    """
    Service interne pour vérifier le socle de validité d'un agent.
    Retourne un dictionnaire détaillé.
    """
    today = timezone.now().date()
    socle_est_valide = True
    checklist = []
    
    # Vérification Médicale
    certificat = CertificatMed.objects.filter(agent=agent).order_by('-date_visite').first()
    echeance_med = getattr(certificat, 'date_expiration_aptitude', None)
    med_valide = certificat and echeance_med and echeance_med >= today
    if not med_valide: socle_est_valide = False
    checklist.append({'nom': 'Aptitude Médicale', 'valide': med_valide, 'details': f"Expire le {echeance_med.strftime('%d/%m/%Y')}" if med_valide else "Manquant ou expiré"})

    # Vérification Linguistique
    mention_ling = MentionLinguistique.objects.filter(brevet__agent=agent, langue='ANGLAIS').first()
    echeance_ling = getattr(mention_ling, 'date_echeance', None)
    ling_valide = mention_ling and echeance_ling and echeance_ling >= today
    if not ling_valide: socle_est_valide = False
    checklist.append({'nom': 'Aptitude Linguistique', 'valide': ling_valide, 'details': f"Expire le {echeance_ling.strftime('%d/%m/%Y')}" if ling_valide else "Manquant ou expiré"})

    # Vérification RAF AERO
    raf_aero = SuiviFormationReglementaire.objects.filter(brevet__agent=agent, formation__slug='fh-raf-aero').first()
    echeance_raf = getattr(raf_aero, 'date_echeance', None)
    raf_valide = raf_aero and echeance_raf and echeance_raf >= today
    if not raf_valide: socle_est_valide = False
    checklist.append({'nom': 'Formation RAF AERO', 'valide': raf_valide, 'details': f"Expire le {echeance_raf.strftime('%d/%m/%Y')}" if raf_valide else "Manquant ou expiré"})
    
    # Extraction des motifs en cas d'invalidité
    motifs = [item['nom'] for item in checklist if not item['valide']]

    return {'est_valide': socle_est_valide, 'motifs': motifs, 'checklist': checklist}

def is_agent_apte_for_flux(agent, flux, on_date):
    """
    Vérifie si un agent est apte à contrôler sur un flux donné à une date donnée.
    Retourne (True, "") si c'est bon, ou (False, "Message d'erreur") si non.
    """
    # Étape 1: Vérifier le socle de l'agent
    socle_context = calculer_statut_socle(agent)
    if not socle_context['est_valide']:
        motif = socle_context['motifs'][0] if socle_context['motifs'] else "Socle invalide"
        return False, f"Socle de l'agent invalide ({motif})."

    # Étape 2: Trouver la MUA correspondante et vérifier son statut
    type_flux_mua = 'CAM' if flux in ['CAM'] else 'CAG'
    
    try:
        mua = MentionUniteAnnuelle.objects.get(
            qualification__brevet__agent=agent,
            type_flux=type_flux_mua,
            date_debut_cycle__lte=on_date,
            date_fin_cycle__gte=on_date,
        )
        if mua.statut != 'ACTIF':
            return False, f"MUA {type_flux_mua} non active (statut: {mua.get_statut_display()})."
            
    except MentionUniteAnnuelle.DoesNotExist:
        return False, f"Aucune MUA {type_flux_mua} valide trouvée pour cette période."
    except MentionUniteAnnuelle.MultipleObjectsReturned:
        return False, "Erreur de données : Plusieurs MUA actives trouvées pour la même période."

    # Si tous les contrôles passent
    return True, ""