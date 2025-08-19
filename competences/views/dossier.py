# Fichier : competences/views/dossier.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.utils import timezone
from django.contrib import messages
from datetime import date
from core.decorators import effective_permission_required

from core.models import Agent
from ..models import Licence, MentionUnite, HistoriqueCompetence
from ..filters import CompetenceFilter

@login_required
def dossier_competence_view(request, agent_id):
    """
    Affiche le dossier de compétences complet pour un agent spécifique.
    L'accès est contrôlé par les permissions effectives de l'utilisateur connecté.
    """
    agent_concerne = get_object_or_404(Agent.objects.prefetch_related('certificats_medicaux', 'rendez_vous_medicaux'), pk=agent_id)
    
    licence = Licence.objects.prefetch_related(
        'qualifications',
        Prefetch(
            'mentions_unite',
            queryset=MentionUnite.objects.select_related('qualification_source', 'centre')
        ),
        'mentions_linguistiques',
        'formations_suivies__formation'
    ).filter(agent=agent_concerne).first()
    
    can_view_all = request.effective_perms.competences.view_all_licences
    can_view_centre = request.effective_perms.competences.view_centre_licences
    
    user_is_owner = (request.user.agent_profile == agent_concerne)
    user_is_in_same_centre = (request.centre_agent and request.centre_agent == agent_concerne.centre)

    if not (user_is_owner or can_view_all or (can_view_centre and user_is_in_same_centre)):
        messages.error(request, "Vous n'avez pas l'autorisation de consulter ce dossier de compétences.")
        return redirect('home')
        
    certificat_medical = agent_concerne.certificats_medicaux.first()

    def get_alert_level(echeance_date):
        if not isinstance(echeance_date, date): return 'critique'
        today = timezone.now().date()
        days_left = (echeance_date - today).days
        if days_left <= 30: return 'critique'
        elif days_left <= 90: return 'alerte'
        else: return 'ok'

    if licence:
        for mention in licence.mentions_unite.all():
            mention.alert_level = get_alert_level(mention.date_echeance)

    context = {
        'agent_concerne': agent_concerne,
        'licence': licence,
        'certificat_medical': certificat_medical,
        'rendez_vous_list': agent_concerne.rendez_vous_medicaux.all(),
        'titre': f"Dossier de Compétences de {agent_concerne.trigram}",
        'today': timezone.now().date(),
        
        'can_edit_licence': request.effective_perms.competences.change_licence,
        'can_add_mention': request.effective_perms.competences.add_mentionunite,
    }
    
    return render(request, 'competences/dossier_competence.html', context)


@login_required
def tableau_bord_competences_view(request):
    """
    Affiche le tableau de bord de suivi des compétences, avec un statut de synthèse.
    """
    def get_alert_level(echeance_date):
        """
        Calcule le niveau d'alerte ('critique', 'alerte', 'ok') pour une date d'échéance.
        """
        if not isinstance(echeance_date, date):
            return 'critique'
        
        today = timezone.now().date()
        days_left = (echeance_date - today).days
        
        if days_left < 0:
            return 'critique'
        if days_left <= 30:
            return 'critique'
        elif days_left <= 90:
            return 'alerte'
        else:
            return 'ok'

    # Étape 1 : Requête de base ciblant uniquement les contrôleurs actifs.
    base_queryset = Agent.objects.filter(
        actif=True, 
        type_agent='controleur'
    ).select_related('centre', 'licence')

    # Étape 2 : Filtrage par permissions (local/national).
    can_view_all = request.effective_perms.competences.view_all_licences
    can_view_centre = request.effective_perms.competences.view_centre_licences
    
    if can_view_all:
        agents_a_afficher_qs = base_queryset.order_by('centre__code_centre', 'trigram')
    elif can_view_centre and request.centre_agent:
        agents_a_afficher_qs = base_queryset.filter(centre=request.centre_agent).order_by('trigram')
    else:
        agents_a_afficher_qs = base_queryset.none()
        messages.warning(request, "Vous n'avez pas les permissions nécessaires pour afficher le tableau de bord.")

    # Étape 3 : Application des filtres de recherche de l'utilisateur.
    competence_filter = CompetenceFilter(request.GET, queryset=agents_a_afficher_qs, user=request.user)
    
    # Étape 4 : Récupération des IDs finaux pour la requête optimisée.
    final_agent_ids = competence_filter.qs.values_list('id_agent', flat=True)

    # Étape 5 : Requête finale et optimisée avec prefetch_related.
    agents_list = Agent.objects.filter(id_agent__in=final_agent_ids).select_related(
        'centre', 'licence'
    ).prefetch_related(
        'certificats_medicaux',
        Prefetch(
            'licence__mentions_unite',
            queryset=MentionUnite.objects.select_related('qualification_source', 'centre').exclude(statut=MentionUnite.StatutMention.INACTIVE_MUTATION)
        ),
        'licence__mentions_linguistiques',
        'licence__formations_suivies__formation'
    ).order_by('centre__code_centre', 'trigram')

    # Étape 6 : Enrichissement de chaque objet 'agent' avec les données calculées.
    today = timezone.now().date()
    for agent in agents_list:
        # Initialisation des valeurs par défaut
        agent.cam_mention, agent.cag_mention, agent.fh_formation, agent.eng_mention, agent.certificat_medical = None, None, None, None, None
        agent.statut_synthese = {
            'apte_socle': False,
            'motif_inaptitude_socle': 'Pas de licence',
            'apte_cam': False,
            'apte_cag': False,
        }

        if hasattr(agent, 'licence') and agent.licence:
            # Récupération des objets liés
            agent.cam_mention = next((m for m in agent.licence.mentions_unite.all() if m.type_flux == 'CAM'), None)
            agent.cag_mention = next((m for m in agent.licence.mentions_unite.all() if m.qualification_source and m.qualification_source.type_qualification == 'ACS'), None)
            agent.fh_formation = next((f for f in agent.licence.formations_suivies.all() if f.formation.slug == 'fh-raf-aero'), None)
            agent.eng_mention = next((ml for ml in agent.licence.mentions_linguistiques.all() if ml.langue == 'ANGLAIS'), None)
            agent.certificat_medical = agent.certificats_medicaux.first()

            # Calcul du statut de synthèse
            apte_socle = True
            motif = ''
            if not agent.certificat_medical or not agent.certificat_medical.date_expiration_aptitude or agent.certificat_medical.date_expiration_aptitude < today:
                apte_socle = False
                motif = 'Médical expiré'
            elif not agent.eng_mention or agent.eng_mention.date_echeance < today:
                apte_socle = False
                motif = 'Linguistique expirée'
            elif not agent.fh_formation or agent.fh_formation.date_echeance < today:
                apte_socle = False
                motif = 'Formation FH échue'
            
            agent.statut_synthese['apte_socle'] = apte_socle
            agent.statut_synthese['motif_inaptitude_socle'] = motif

            if apte_socle:
                if agent.cam_mention and agent.cam_mention.is_valide:
                    agent.statut_synthese['apte_cam'] = True
                if agent.cag_mention and agent.cag_mention.is_valide:
                    agent.statut_synthese['apte_cag'] = True

            # Calcul des niveaux d'alerte pour l'affichage
            if agent.cam_mention: agent.cam_mention.alert_level = get_alert_level(agent.cam_mention.date_echeance)
            if agent.cag_mention: agent.cag_mention.alert_level = get_alert_level(agent.cag_mention.date_echeance)
            if agent.certificat_medical: agent.certificat_medical.alert_level = get_alert_level(agent.certificat_medical.date_expiration_aptitude)
            if agent.eng_mention: agent.eng_mention.alert_level = get_alert_level(agent.eng_mention.date_echeance)
            if agent.fh_formation: agent.fh_formation.alert_level = get_alert_level(agent.fh_formation.date_echeance)

    # Étape 7 : Rendu du template
    context = {
        'filter': competence_filter,
        'agents_list': agents_list,
        'titre': "Tableau de Bord des Compétences",
        'today': today,
    }
    
    return render(request, 'competences/tableau_bord.html', context)

@login_required
@effective_permission_required('competences.view_all_licences') # Seuls les nationaux voient l'audit
def journal_audit_competences_view(request):
    """ Affiche le journal des actions automatiques du système de surveillance. """
    
    historique = HistoriqueCompetence.objects.select_related('licence__agent').order_by('-timestamp')
    
    # On pourrait ajouter un filtre par date ici plus tard
    
    context = {
        'historique_list': historique[:200], # On limite aux 200 derniers événements pour la performance
        'titre': "Journal d'Audit du Système de Compétences"
    }
    return render(request, 'competences/journal_audit.html', context)