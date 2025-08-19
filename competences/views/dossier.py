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
    agent_concerne = get_object_or_404(Agent.objects.prefetch_related('certificats_medicaux'), pk=agent_id)
    
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
        'titre': f"Dossier de Compétences de {agent_concerne.trigram}",
        'today': timezone.now().date(),
        
        'can_edit_licence': request.effective_perms.competences.change_licence,
        'can_add_mention': request.effective_perms.competences.add_mentionunite,
    }
    
    return render(request, 'competences/dossier_competence.html', context)


@login_required
def tableau_bord_competences_view(request):
    """
    Affiche le tableau de bord de suivi des compétences.
    - Cible UNIQUEMENT les agents de type 'contrôleur'.
    - Filtre la visibilité (local/national) en fonction des permissions.
    - Applique les filtres de recherche.
    - Enrichit les objets pour le template.
    """
    def get_alert_level(echeance_date):
        if not isinstance(echeance_date, date):
            return 'critique'
        today = timezone.now().date()
        days_left = (echeance_date - today).days
        if days_left <= 30:
            return 'critique'
        elif days_left <= 90:
            return 'alerte'
        else:
            return 'ok'

    # ==========================================================
    #                 MODIFICATION INTÉGRÉE ICI
    # ==========================================================
    
    # Étape 1 : La requête de base cible MAINTENANT uniquement les contrôleurs actifs.
    # On utilise la constante définie dans le modèle Agent pour plus de robustesse.
    base_queryset = Agent.objects.filter(
        actif=True, 
        type_agent='controleur'
    ).select_related('centre', 'licence')

    # Étape 2 : Le filtrage par permissions (local/national) s'applique sur ce sous-ensemble de contrôleurs.
    can_view_all = request.effective_perms.competences.view_all_licences
    can_view_centre = request.effective_perms.competences.view_centre_licences
    
    if can_view_all:
        # Un national (même s'il est administratif) voit tous les CONTRÔLEURS.
        agents_a_afficher_qs = base_queryset.order_by('centre__code_centre', 'trigram')
    elif can_view_centre and request.centre_agent:
        # Un responsable local ne voit que les CONTRÔLEURS de son propre centre.
        agents_a_afficher_qs = base_queryset.filter(centre=request.centre_agent).order_by('trigram')
    else:
        agents_a_afficher_qs = base_queryset.none()
        messages.warning(request, "Vous n'avez pas les permissions nécessaires pour afficher le tableau de bord.")

    # Le reste de la vue est identique, car la logique de filtrage et d'enrichissement
    # s'applique maintenant sur la bonne liste d'agents.
    
    competence_filter = CompetenceFilter(request.GET, queryset=agents_a_afficher_qs, user=request.user)
    
    final_agent_ids = competence_filter.qs.values_list('id_agent', flat=True)

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

    for agent in agents_list:
        if hasattr(agent, 'licence') and agent.licence:
            agent.cam_mention = next((m for m in agent.licence.mentions_unite.all() if m.type_flux == 'CAM'), None)
            agent.cag_mention = next((m for m in agent.licence.mentions_unite.all() if m.qualification_source and m.qualification_source.type_qualification == 'ACS'), None)
            agent.fh_formation = next((f for f in agent.licence.formations_suivies.all() if f.formation.nom == "Facteurs Humains RAF Aéro"), None)
            agent.eng_mention = next((ml for ml in agent.licence.mentions_linguistiques.all() if ml.langue == 'ANGLAIS'), None)
            
            agent.certificat_medical = agent.certificats_medicaux.first()

            if agent.cam_mention: agent.cam_mention.alert_level = get_alert_level(agent.cam_mention.date_echeance)
            if agent.cag_mention: agent.cag_mention.alert_level = get_alert_level(agent.cag_mention.date_echeance)
            if agent.certificat_medical: agent.certificat_medical.alert_level = get_alert_level(agent.certificat_medical.validite)
            if agent.eng_mention: agent.eng_mention.alert_level = get_alert_level(agent.eng_mention.date_echeance)
            if agent.fh_formation: agent.fh_formation.alert_level = get_alert_level(agent.fh_formation.date_echeance)
        else:
            agent.cam_mention, agent.cag_mention, agent.fh_formation, agent.eng_mention, agent.certificat_medical = None, None, None, None, None

    context = {
        'filter': competence_filter,
        'agents_list': agents_list,
        'titre': "Tableau de Bord des Compétences",
        'today': timezone.now().date(),
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