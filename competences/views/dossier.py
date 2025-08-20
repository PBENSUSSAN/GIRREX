# Fichier : competences/views/dossier.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date

from core.decorators import effective_permission_required
from core.models import Agent, CertificatMed
from ..models import Brevet, Qualification, MentionUniteAnnuelle, EvenementCarriere, MentionLinguistique, SuiviFormationReglementaire
from ..filters import CompetenceFilter


# ==========================================================
# FONCTION DE SERVICE POUR CALCULER L'ÉTAT DU SOCLE
# ==========================================================
def calculer_statut_socle(agent):
    """
    Calcule l'état du socle de validité pour un agent donné.
    Renvoie un dictionnaire avec le statut et les détails.
    """
    today = timezone.now().date()
    socle = {
        'est_valide': True,
        'motifs': [],
        'details': {}
    }

    # 1. Vérification Médicale
    certificat = CertificatMed.objects.filter(agent=agent).order_by('-date_visite').first()
    if not certificat or not certificat.date_expiration_aptitude or certificat.date_expiration_aptitude < today:
        socle['est_valide'] = False
        socle['motifs'].append('Médical expiré')
    socle['details']['certificat_medical'] = certificat

    # 2. Vérification Linguistique (Anglais)
    mention_ling = MentionLinguistique.objects.filter(brevet__agent=agent, langue='ANGLAIS').first()
    if not mention_ling or mention_ling.date_echeance < today:
        socle['est_valide'] = False
        socle['motifs'].append('Linguistique expirée')
    socle['details']['mention_linguistique'] = mention_ling

    # 3. Vérification RAF AERO
    raf_aero = SuiviFormationReglementaire.objects.filter(brevet__agent=agent, formation__slug='fh-raf-aero').first()
    if not raf_aero or raf_aero.date_echeance < today:
        socle['est_valide'] = False
        socle['motifs'].append('RAF AERO échue')
    socle['details']['raf_aero'] = raf_aero
    
    return socle


@login_required
def tableau_bord_view(request):
    """
    Affiche le tableau de bord centré sur les Agents, avec leurs MUA dépliables.
    """
    # On récupère toutes les MUA actives et on précharge toutes les données liées
    muas_actives = MentionUniteAnnuelle.objects.filter(
        statut='ACTIF',
        qualification__isnull=False,
        qualification__brevet__isnull=False,
        qualification__brevet__agent__isnull=False 
    ).select_related(
        'qualification__brevet__agent',
        'qualification__centre'
    ).order_by('qualification__brevet__agent__trigram') # Important de trier par agent

    # Dictionnaire pour regrouper les MUA par agent
    agents_dict = {}

    for mua in muas_actives:
        agent = mua.qualification.brevet.agent
        
        # Si c'est la première fois qu'on voit cet agent, on l'ajoute au dictionnaire
        if agent.id_agent not in agents_dict:
            agents_dict[agent.id_agent] = {
                'agent_obj': agent,
                'statut_socle': calculer_statut_socle(agent),
                'muas': []
            }
        
        # On ajoute la MUA à la liste des MUA de cet agent
        # (on pourrait y ajouter le calcul de progression ici si besoin)
        agents_dict[agent.id_agent]['muas'].append(mua)

    context = {
        # On passe la liste des valeurs du dictionnaire au template
        'agents_list': list(agents_dict.values()),
        'titre': "Tableau de Bord des Compétences"
    }
    return render(request, 'competences/tableau_bord.html', context)


# La vue dossier_agent_view reste la même pour l'instant
@login_required
def dossier_agent_view(request, agent_id):
    """
    Affiche le dossier de compétences complet pour un agent spécifique.
    C'est la nouvelle vue centrale de consultation.
    """
    agent = get_object_or_404(Agent, pk=agent_id)
    brevet = Brevet.objects.filter(agent=agent).first()
    
    qualifications_par_centre = {}
    if brevet:
        qualifications = Qualification.objects.filter(brevet=brevet).order_by('centre__code_centre', 'date_obtention')
        for q in qualifications:
            if q.centre not in qualifications_par_centre:
                qualifications_par_centre[q.centre] = []
            qualifications_par_centre[q.centre].append(q)

    # On calcule le statut du socle ici aussi pour l'afficher dans le dossier
    statut_socle = calculer_statut_socle(agent)

    context = {
        'agent_concerne': agent,
        'brevet': brevet,
        'qualifications_par_centre': qualifications_par_centre,
        'muas_actives': MentionUniteAnnuelle.objects.filter(qualification__brevet=brevet, statut='ACTIF'),
        'evenements_carriere': EvenementCarriere.objects.filter(agent=agent),
        'statut_socle': statut_socle, # On passe le statut du socle au template
        'titre': f"Dossier de Compétences de {agent.trigram}"
    }
    
    return render(request, 'competences/dossier_competence.html', context)


# La vue journal_audit_view reste la même pour l'instant
@login_required
def journal_audit_view(request):
    """ Vue pour le journal d'audit (à redéfinir). """
    context = {'titre': "Journal d'Audit"}
    return render(request, 'competences/journal_audit.html', context)

