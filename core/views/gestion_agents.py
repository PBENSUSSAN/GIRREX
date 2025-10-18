# Fichier : core/views/gestion_agents.py
# Vues pour la gestion des agents par le Chef de Centre

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from datetime import date

from core.models import Agent, Centre, Role, ArretMaladie
from core.decorators import effective_permission_required


def peut_gerer_agents_centre(request, centre):
    """
    Vérifie si l'utilisateur peut gérer les agents du centre.
    UNIQUEMENT Chef de Centre ou Adjoint Chef de Centre.
    """
    if not request.active_agent_role:
        return False
    
    # UNIQUEMENT Chef de Centre ou Adjoint Chef de Centre
    if request.active_agent_role.role.nom not in [
        Role.RoleName.CHEF_DE_CENTRE,
        Role.RoleName.ADJOINT_CHEF_DE_CENTRE
    ]:
        return False
    
    # Du même centre
    if not request.centre_agent:
        return False
    
    return request.centre_agent.id == centre.id


@login_required
def liste_agents_centre_view(request, centre_id):
    """
    Liste de tous les agents du centre pour gestion.
    Accès : Chef de Centre et Adjoint Chef de Centre uniquement.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    
    # Vérification permissions
    if not peut_gerer_agents_centre(request, centre):
        raise PermissionDenied("Seul le Chef de Centre ou son Adjoint peut accéder à cette page.")
    
    # Récupérer tous les agents du centre
    agents_queryset = Agent.objects.filter(centre=centre)
    
    # Filtres
    filtre_statut = request.GET.get('statut', 'actif')
    filtre_fonction = request.GET.get('fonction', '')
    filtre_arret = request.GET.get('arret', '')
    recherche = request.GET.get('q', '')
    
    # Appliquer filtre statut
    if filtre_statut == 'actif':
        agents_queryset = agents_queryset.filter(actif=True)
    elif filtre_statut == 'inactif':
        agents_queryset = agents_queryset.filter(actif=False)
    # Si 'tous', on ne filtre pas
    
    # Appliquer filtre fonction (basé sur type_agent)
    if filtre_fonction:
        agents_queryset = agents_queryset.filter(type_agent=filtre_fonction)
    
    # Appliquer recherche
    if recherche:
        agents_queryset = agents_queryset.filter(
            Q(trigram__icontains=recherche) |
            Q(nom__icontains=recherche) |
            Q(prenom__icontains=recherche)
        )
    
    # Récupérer tous les agents avec leurs arrêts en cours
    agents_list = []
    for agent in agents_queryset.order_by('trigram'):
        arret_en_cours = None
        try:
            # Essayer de récupérer un arrêt EN_COURS
            arret_en_cours = agent.arrets_maladie.filter(statut='EN_COURS').first()
        except Exception as e:
            # Si erreur (champ statut n'existe pas encore), continuer
            print(f"Erreur récupération arrêt pour {agent.trigram}: {e}")
            pass
        
        agents_list.append({
            'agent': agent,
            'arret_en_cours': arret_en_cours,
            'a_arret': arret_en_cours is not None
        })
    
    # Filtre arrêt en cours
    if filtre_arret == 'en_arret':
        agents_list = [a for a in agents_list if a['a_arret']]
    elif filtre_arret == 'sans_arret':
        agents_list = [a for a in agents_list if not a['a_arret']]
    
    # Statistiques
    total_agents = len(agents_list)
    nb_en_arret = sum(1 for a in agents_list if a['a_arret'])
    
    # Liste des types d'agents pour le filtre
    fonctions_disponibles = Agent.objects.filter(
        centre=centre,
        actif=True
    ).values_list('type_agent', flat=True).distinct().order_by('type_agent')
    
    context = {
        'centre': centre,
        'agents_list': agents_list,
        'titre': f"Gestion des Agents - {centre.code_centre}",
        'stats': {
            'total': total_agents,
            'en_arret': nb_en_arret,
            'disponibles': total_agents - nb_en_arret
        },
        'filtres': {
            'statut': filtre_statut,
            'fonction': filtre_fonction,
            'arret': filtre_arret,
            'recherche': recherche
        },
        'fonctions_disponibles': fonctions_disponibles,
    }
    
    return render(request, 'core/gestion_agents/liste_agents.html', context)


@login_required
def fiche_agent_view(request, centre_id, agent_id):
    """
    Fiche complète d'un agent avec toutes les actions possibles.
    Hub central pour la gestion d'un agent.
    Accès : Chef de Centre et Adjoint Chef de Centre uniquement.
    """
    centre = get_object_or_404(Centre, pk=centre_id)
    agent = get_object_or_404(Agent, pk=agent_id)
    
    # Vérification permissions
    if not peut_gerer_agents_centre(request, centre):
        raise PermissionDenied("Seul le Chef de Centre ou son Adjoint peut accéder à cette page.")
    
    # Vérifier que l'agent appartient bien au centre
    if agent.centre != centre:
        raise PermissionDenied("Cet agent n'appartient pas à votre centre.")
    
    # Récupérer les informations
    certificat_actuel = agent.certificat_medical_actif()
    
    # Statut médical
    statut_medical = {
        'est_valide': False,
        'libelle': 'Inconnu',
        'classe': 'secondary',
        'expiration': None,
        'jours_restants': None
    }
    
    if certificat_actuel:
        if certificat_actuel.resultat == 'APTE' and certificat_actuel.est_valide_aujourdhui:
            statut_medical['est_valide'] = True
            statut_medical['libelle'] = 'APTE'
            statut_medical['classe'] = 'success'
            statut_medical['expiration'] = certificat_actuel.date_expiration_aptitude
            statut_medical['jours_restants'] = certificat_actuel.jours_avant_expiration
            
            # Alerte selon échéance
            if statut_medical['jours_restants'] and statut_medical['jours_restants'] <= 30:
                statut_medical['classe'] = 'danger'
            elif statut_medical['jours_restants'] and statut_medical['jours_restants'] <= 90:
                statut_medical['classe'] = 'warning'
        
        elif certificat_actuel.resultat == 'INAPTE_TEMP':
            statut_medical['libelle'] = 'INAPTE TEMPORAIRE'
            statut_medical['classe'] = 'warning'
        elif certificat_actuel.resultat == 'INAPTE_DEF':
            statut_medical['libelle'] = 'INAPTE DÉFINITIF'
            statut_medical['classe'] = 'danger'
    
    # Arrêts en cours
    arrets_en_cours = []
    try:
        arrets_en_cours = list(agent.arrets_maladie.filter(statut='EN_COURS').order_by('-date_debut'))
        print(f">>> Arrêts trouvés pour {agent.trigram}: {len(arrets_en_cours)}")
    except Exception as e:
        print(f">>> ERREUR récupération arrêts pour {agent.trigram}: {e}")
        pass
    
    # MUA actives
    muas_actives = []
    if hasattr(agent, 'brevets'):
        from competences.models import MentionUniteAnnuelle
        for brevet in agent.brevets.all():
            for qualification in brevet.qualifications.all():
                muas = qualification.muas.filter(statut='ACTIF')
                muas_actives.extend(muas)
    
    # Prochain RDV
    prochain_rdv = agent.rendez_vous_medicaux.filter(
        statut='PLANIFIE',
        date_heure_rdv__gte=date.today()
    ).order_by('date_heure_rdv').first()
    
    # Dernière activité (dernier vol)
    derniere_activite = None
    if hasattr(agent, 'saisies_activite'):
        try:
            derniere_saisie = agent.saisies_activite.filter(
                statut_validation='VALIDE'
            ).order_by('-date_activite').first()
            if derniere_saisie:
                derniere_activite = derniere_saisie.date_activite
        except:
            pass
    
    context = {
        'centre': centre,
        'agent': agent,
        'titre': f"Fiche Agent - {agent.trigram}",
        'statut_medical': statut_medical,
        'arrets_en_cours': arrets_en_cours,
        'muas_actives': muas_actives,
        'prochain_rdv': prochain_rdv,
        'derniere_activite': derniere_activite,
        'certificat_actuel': certificat_actuel,
    }
    
    return render(request, 'core/gestion_agents/fiche_agent.html', context)
