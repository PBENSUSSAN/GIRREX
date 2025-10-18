# Fichier : core/views/medical.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from datetime import date, timedelta
from django.utils import timezone

from core.decorators import effective_permission_required
from core.models import Agent, RendezVousMedical, CertificatMed, ArretMaladie, Centre, Role, HistoriqueRDV
from ..forms import RendezVousMedicalForm, CertificatMedForm, ArretMaladieForm

# ============================================================================
# VUES RDV - Planification et gestion (RÉÉCRITURE AVEC TRAÇABILITÉ)
# ============================================================================

@login_required
def planifier_rdv_medical_view(request, agent_id=None):
    """
    Permet à un agent de planifier son propre RDV.
    Si agent_id fourni : FORM_LOCAL peut planifier pour un agent.
    """
    if agent_id:
        # FORM_LOCAL planifie pour un agent de son centre
        agent = get_object_or_404(Agent, pk=agent_id)
        
        # Vérifier les permissions
        if not peut_voir_dossier_medical(request, agent):
            raise PermissionDenied("Vous n'avez pas l'autorisation de planifier un RDV pour cet agent.")
        
        if 'competences.change_licence' not in request.effective_perms:
            raise PermissionDenied("Seul le FORM_LOCAL peut planifier un RDV pour un autre agent.")
    else:
        # Agent planifie pour lui-même
        if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
            raise PermissionDenied("Vous devez être un agent pour planifier un RDV.")
        agent = request.user.agent_profile
    
    if request.method == 'POST':
        form = RendezVousMedicalForm(request.POST)
        if form.is_valid():
            rdv = form.save(commit=False)
            rdv.agent = agent
            rdv.created_by = request.user
            rdv.modified_by = request.user
            rdv.statut = RendezVousMedical.StatutRDV.PLANIFIE
            rdv.save()
            
            # Créer l'entrée d'historique
            HistoriqueRDV.objects.create(
                rdv=rdv,
                action=HistoriqueRDV.TypeAction.CREATION,
                utilisateur=request.user,
                nouveau_statut=rdv.statut,
                nouvelle_date=rdv.date_heure_rdv,
                commentaire=f"RDV planifié pour {agent.trigram}"
            )
            
            messages.success(
                request,
                f"Rendez-vous médical planifié avec succès pour {agent.trigram} le {rdv.date_heure_rdv.strftime('%d/%m/%Y à %Hh%M')}."
            )
            
            return redirect('dossier_medical', agent_id=agent.id_agent)
    else:
        form = RendezVousMedicalForm()
    
    context = {
        'form': form,
        'agent_concerne': agent,
        'titre': f"Planifier un RDV Médical - {agent.trigram}",
        'action': 'planifier'
    }
    
    return render(request, 'core/medical/form_rdv.html', context)


@login_required
def modifier_rdv_medical_view(request, rdv_id):
    """
    Permet à l'agent de modifier son RDV (report).
    FORM_LOCAL peut aussi modifier.
    """
    rdv = get_object_or_404(RendezVousMedical, pk=rdv_id)
    agent = rdv.agent
    
    # Vérifier les permissions
    if request.user.agent_profile != agent:
        # Ce n'est pas l'agent lui-même, vérifier si c'est le FORM_LOCAL
        if not peut_voir_dossier_medical(request, agent):
            raise PermissionDenied("Vous n'avez pas l'autorisation de modifier ce RDV.")
        if 'competences.change_licence' not in request.effective_perms:
            raise PermissionDenied("Seul l'agent ou le FORM_LOCAL peut modifier ce RDV.")
    
    # Empêcher la modification d'un RDV déjà réalisé ou annulé
    if rdv.statut in [RendezVousMedical.StatutRDV.REALISE, RendezVousMedical.StatutRDV.ANNULE]:
        messages.error(request, "Ce RDV ne peut plus être modifié (déjà réalisé ou annulé).")
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    # Sauvegarder l'ancienne date pour l'historique
    ancienne_date = rdv.date_heure_rdv
    ancien_statut = rdv.statut
    
    if request.method == 'POST':
        form = RendezVousMedicalForm(request.POST, instance=rdv)
        if form.is_valid():
            rdv = form.save(commit=False)
            rdv.modified_by = request.user
            
            # Si la date a changé, passer en REPORTE
            if rdv.date_heure_rdv != ancienne_date:
                rdv.statut = RendezVousMedical.StatutRDV.REPORTE
            
            rdv.save()
            
            # Créer l'entrée d'historique
            HistoriqueRDV.objects.create(
                rdv=rdv,
                action=HistoriqueRDV.TypeAction.MODIFICATION,
                utilisateur=request.user,
                ancien_statut=ancien_statut,
                nouveau_statut=rdv.statut,
                ancienne_date=ancienne_date,
                nouvelle_date=rdv.date_heure_rdv,
                commentaire="RDV reporté" if rdv.date_heure_rdv != ancienne_date else "RDV modifié"
            )
            
            messages.success(
                request,
                f"RDV modifié avec succès. Nouvelle date : {rdv.date_heure_rdv.strftime('%d/%m/%Y à %Hh%M')}."
            )
            
            return redirect('dossier_medical', agent_id=agent.id_agent)
    else:
        form = RendezVousMedicalForm(instance=rdv)
    
    context = {
        'form': form,
        'agent_concerne': agent,
        'rdv': rdv,
        'titre': f"Modifier le RDV - {agent.trigram}",
        'action': 'modifier'
    }
    
    return render(request, 'core/medical/form_rdv.html', context)


@login_required
def annuler_rdv_medical_view(request, rdv_id):
    """
    Permet d'annuler un RDV (ne supprime pas, change le statut).
    """
    rdv = get_object_or_404(RendezVousMedical, pk=rdv_id)
    agent = rdv.agent
    
    # Vérifier les permissions
    if request.user.agent_profile != agent:
        if not peut_voir_dossier_medical(request, agent):
            raise PermissionDenied("Vous n'avez pas l'autorisation d'annuler ce RDV.")
        if 'competences.change_licence' not in request.effective_perms:
            raise PermissionDenied("Seul l'agent ou le FORM_LOCAL peut annuler ce RDV.")
    
    if rdv.statut == RendezVousMedical.StatutRDV.REALISE:
        messages.error(request, "Ce RDV ne peut pas être annulé (déjà réalisé).")
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    if request.method == 'POST':
        ancien_statut = rdv.statut
        rdv.statut = RendezVousMedical.StatutRDV.ANNULE
        rdv.modified_by = request.user
        rdv.save()
        
        # Créer l'entrée d'historique
        HistoriqueRDV.objects.create(
            rdv=rdv,
            action=HistoriqueRDV.TypeAction.ANNULATION,
            utilisateur=request.user,
            ancien_statut=ancien_statut,
            nouveau_statut=rdv.statut,
            commentaire=request.POST.get('raison', '')
        )
        
        messages.warning(
            request,
            f"RDV du {rdv.date_heure_rdv.strftime('%d/%m/%Y')} annulé."
        )
        
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    context = {
        'rdv': rdv,
        'agent_concerne': agent,
        'titre': f"Annuler le RDV - {agent.trigram}"
    }
    
    return render(request, 'core/medical/annuler_rdv.html', context)


@login_required
def saisir_resultat_visite_view(request, rdv_id):
    """
    Permet à l'agent de saisir le résultat de sa visite.
    FORM_LOCAL peut aussi saisir.
    CR optionnel.
    """
    rdv = get_object_or_404(RendezVousMedical, pk=rdv_id)
    agent = rdv.agent
    
    # Vérifier les permissions
    if request.user.agent_profile != agent:
        if not peut_voir_dossier_medical(request, agent):
            raise PermissionDenied("Vous n'avez pas l'autorisation de saisir le résultat de ce RDV.")
        if 'competences.change_licence' not in request.effective_perms:
            raise PermissionDenied("Seul l'agent ou le FORM_LOCAL peut saisir le résultat.")
    
    # Si le RDV est annulé, bloquer
    if rdv.statut == RendezVousMedical.StatutRDV.ANNULE:
        messages.error(request, "Ce RDV a été annulé, impossible de saisir un résultat.")
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    # Si un certificat existe déjà, on modifie
    instance = rdv.certificat_genere
    
    if request.method == 'POST':
        form = CertificatMedForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            certificat = form.save(commit=False)
            certificat.agent = agent
            certificat.saisi_par = request.user
            certificat.save()
            
            # Lier le certificat au RDV
            ancien_statut = rdv.statut
            rdv.certificat_genere = certificat
            rdv.statut = RendezVousMedical.StatutRDV.REALISE
            rdv.modified_by = request.user
            rdv.save()
            
            # Créer l'entrée d'historique
            HistoriqueRDV.objects.create(
                rdv=rdv,
                action=HistoriqueRDV.TypeAction.REALISATION,
                utilisateur=request.user,
                ancien_statut=ancien_statut,
                nouveau_statut=rdv.statut,
                commentaire=f"Résultat : {certificat.get_resultat_display()}"
            )
            
            messages.success(
                request,
                f"Résultat de la visite enregistré avec succès pour {agent.trigram}. Statut : {certificat.get_resultat_display()}."
            )
            
            return redirect('dossier_medical', agent_id=agent.id_agent)
    else:
        # Pré-remplir avec les données du RDV
        initial_data = {
            'date_visite': rdv.date_heure_rdv.date(),
            'organisme_medical': rdv.organisme_medical
        }
        form = CertificatMedForm(instance=instance, initial=initial_data if not instance else None)
    
    context = {
        'form': form,
        'agent_concerne': agent,
        'rdv': rdv,
        'titre': f"Saisir le Résultat de la Visite - {agent.trigram}"
    }
    
    return render(request, 'core/medical/form_resultat.html', context)


@login_required
def historique_rdv_view(request, rdv_id):
    """
    Affiche l'historique complet d'un RDV (auditabilité).
    """
    rdv = get_object_or_404(RendezVousMedical, pk=rdv_id)
    agent = rdv.agent
    
    # Vérifier les permissions
    if not peut_voir_dossier_medical(request, agent):
        raise PermissionDenied("Vous n'avez pas l'autorisation de voir cet historique.")
    
    historique = rdv.historique.all().order_by('-date_action')
    
    context = {
        'rdv': rdv,
        'agent_concerne': agent,
        'historique': historique,
        'titre': f"Historique du RDV - {agent.trigram}"
    }
    
    return render(request, 'core/medical/historique_rdv.html', context)


# ============================================================================
# NOUVELLES VUES - Module Suivi Médical Enrichi
# ============================================================================

def peut_voir_dossier_medical(request, agent_cible):
    """
    Vérifie si l'utilisateur peut voir le dossier médical de l'agent cible.
    
    UTILISE UNIQUEMENT request.effective_perms (calculé par le middleware)
    """
    if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
        return False
    
    agent_user = request.user.agent_profile
    
    # 1. L'agent voit SON propre dossier
    if agent_user.id_agent == agent_cible.id_agent:
        return True
    
    # 2. Chef Division/Adjoint Chef Division/Adjoint Form (vision nationale)
    if 'competences.view_all_licences' in request.effective_perms:
        return True
    
    # 2bis. Vérification explicite par rôle (au cas où la permission n'est pas encore assignée)
    if request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_FORM
    ]:
        return True
    
    # 3. FORM_LOCAL (peut modifier) → voit son centre
    if 'competences.change_licence' in request.effective_perms:
        if request.centre_agent and agent_cible.centre:
            if request.centre_agent.id == agent_cible.centre.id:
                return True
    
    # 4. Chef de Centre / Adjoint Chef de Centre (consultation de leur centre)
    if request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.CHEF_DE_CENTRE,
        Role.RoleName.ADJOINT_CHEF_DE_CENTRE
    ]:
        if request.centre_agent and agent_cible.centre:
            if request.centre_agent.id == agent_cible.centre.id:
                return True
    
    return False


def peut_gerer_arret_maladie(request, agent_cible):
    """
    Vérifie si l'utilisateur peut gérer les arrêts maladie de l'agent cible.
    
    UNIQUEMENT Chef de Centre ou Adjoint Chef de Centre du CENTRE de l'agent.
    """
    if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
        return False
    
    if not request.active_agent_role:
        return False
    
    # UNIQUEMENT Chef de Centre ou Adjoint Chef de Centre
    if request.active_agent_role.role.nom not in [
        Role.RoleName.CHEF_DE_CENTRE,
        Role.RoleName.ADJOINT_CHEF_DE_CENTRE
    ]:
        return False
    
    # Du même centre que l'agent
    if not request.centre_agent or not agent_cible.centre:
        return False
    
    return request.centre_agent.id == agent_cible.centre.id


@login_required
def dossier_medical_view(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    
    if not peut_voir_dossier_medical(request, agent):
        raise PermissionDenied("Vous n'avez pas l'autorisation d'accéder à ce dossier médical.")
    
    certificat_actuel = agent.certificat_medical_actif()
    
    statut_info = {
        'est_valide': False,
        'classe': 'danger',
        'badge_classe': 'bg-danger',
        'libelle': 'INAPTE',
        'expiration': None,
        'jours_restants': None,
        'restrictions': []
    }
    
    if certificat_actuel:
        if certificat_actuel.resultat == 'APTE' and certificat_actuel.est_valide_aujourdhui:
            statut_info['est_valide'] = True
            statut_info['classe'] = 'success'
            statut_info['badge_classe'] = 'bg-success'  # Le badge reste TOUJOURS vert si APTE
            statut_info['libelle'] = 'APTE'
            statut_info['expiration'] = certificat_actuel.date_expiration_aptitude
            statut_info['jours_restants'] = certificat_actuel.jours_avant_expiration
            
            # Changer la CLASSE (header) selon l'échéance, mais pas le badge
            if statut_info['jours_restants'] is not None:
                if statut_info['jours_restants'] <= 30:
                    statut_info['classe'] = 'danger'  # Header rouge
                elif statut_info['jours_restants'] <= 90:
                    statut_info['classe'] = 'warning'  # Header orange
        
        elif certificat_actuel.resultat == 'INAPTE_TEMP':
            statut_info['libelle'] = 'INAPTE TEMPORAIRE'
            statut_info['badge_classe'] = 'bg-warning'
        
        if certificat_actuel.restrictions:
            statut_info['restrictions'] = [
                r.strip() for r in certificat_actuel.restrictions.split('\n') if r.strip()
            ]
    
    historique_certificats = agent.certificats_medicaux.all().order_by('-date_visite')
    prochain_rdv = agent.rendez_vous_medicaux.filter(
        statut='PLANIFIE',
        date_heure_rdv__gte=date.today()
    ).order_by('date_heure_rdv').first()
    
    # Arrêts EN COURS uniquement
    arrets_en_cours = agent.arrets_maladie.filter(
        statut='EN_COURS'
    ).order_by('-date_debut') if hasattr(agent.arrets_maladie.first(), 'statut') else []
    
    # Arrêts récents (6 derniers mois) - tous statuts sauf EN_COURS
    six_mois_avant = date.today() - timedelta(days=180)
    arrets_recents = agent.arrets_maladie.filter(
        date_debut__gte=six_mois_avant
    ).exclude(
        statut='EN_COURS'
    ).order_by('-date_debut') if hasattr(agent.arrets_maladie.first(), 'statut') else agent.arrets_maladie.filter(date_debut__gte=six_mois_avant).order_by('-date_debut')
    
    # Vérifier si l'utilisateur peut gérer les arrêts
    peut_gerer_arrets = peut_gerer_arret_maladie(request, agent)
    
    context = {
        'agent_concerne': agent,
        'titre': f"Dossier Médical - {agent.trigram}",
        'statut_info': statut_info,
        'historique_certificats': historique_certificats,
        'prochain_rdv': prochain_rdv,
        'arrets_en_cours': arrets_en_cours,
        'arrets_recents': arrets_recents,
        'peut_gerer_arrets': peut_gerer_arrets,
    }
    
    return render(request, 'core/medical/dossier_medical.html', context)


@login_required
def dashboard_medical_centre_view(request, centre_id):
    centre = get_object_or_404(Centre, pk=centre_id)
    
    # Vérification des permissions
    acces_autorise = False
    
    # 1. Chef de Division ou Adjoint Chef de Division → Accès à TOUS les centres
    if request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_CHEF_DE_DIVISION
    ]:
        acces_autorise = True
        print(">>> ACCÈS AUTORISÉ : Chef de Division")
    
    # 2. Permission view_all_licences → Accès à TOUS les centres
    elif 'competences.view_all_licences' in request.effective_perms:
        acces_autorise = True
        print(">>> ACCÈS AUTORISÉ : Permission view_all_licences")
    
    # 3. FORM_LOCAL, Chef de Centre, Adjoint Chef de Centre → Accès à LEUR centre uniquement
    elif request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.FORM_LOCAL,
        Role.RoleName.CHEF_DE_CENTRE,
        Role.RoleName.ADJOINT_CHEF_DE_CENTRE
    ]:
        # Vérifier que c'est bien leur centre
        if request.centre_agent and request.centre_agent.id == centre.id:
            acces_autorise = True
            print(f">>> ACCÈS AUTORISÉ : {request.active_agent_role.role.nom} de ce centre")
        else:
            print(f">>> ACCÈS REFUSÉ : Pas le bon centre (agent au centre {request.centre_agent.id if request.centre_agent else 'NONE'}, demandé {centre.id})")
    else:
        print(">>> ACCÈS REFUSÉ : Aucune condition remplie")
    
    # Refuser l'accès si aucune condition n'est remplie
    if not acces_autorise:
        raise PermissionDenied("Vous n'avez pas l'autorisation d'accéder au dashboard médical de ce centre.")
    
    agents_centre = Agent.objects.filter(centre=centre, actif=True).order_by('trigram')
    today = date.today()
    
    alertes_critiques = []
    alertes_urgentes = []
    alertes_importantes = []
    agents_ok = []
    
    for agent_item in agents_centre:
        cert = agent_item.certificat_medical_actif()
        agent_info = {
            'agent': agent_item,
            'certificat': cert,
            'jours_restants': None,
            'statut': 'inconnu',
            'classe_alerte': 'secondary'
        }
        
        if not cert:
            agent_info['statut'] = 'aucun_certificat'
            agent_info['classe_alerte'] = 'danger'
            alertes_critiques.append(agent_info)
            continue
        
        if cert.resultat != 'APTE':
            agent_info['statut'] = 'inapte'
            agent_info['classe_alerte'] = 'danger'
            alertes_critiques.append(agent_info)
            continue
        
        if not cert.date_expiration_aptitude:
            agent_info['statut'] = 'pas_expiration'
            agent_info['classe_alerte'] = 'warning'
            alertes_urgentes.append(agent_info)
            continue
        
        jours_restants = (cert.date_expiration_aptitude - today).days
        agent_info['jours_restants'] = jours_restants
        
        if jours_restants < 0:
            agent_info['statut'] = 'expire'
            agent_info['classe_alerte'] = 'danger'
            alertes_critiques.append(agent_info)
        elif jours_restants <= 30:
            agent_info['statut'] = 'expire_bientot'
            agent_info['classe_alerte'] = 'danger'
            alertes_urgentes.append(agent_info)
        elif jours_restants <= 90:
            agent_info['statut'] = 'a_surveiller'
            agent_info['classe_alerte'] = 'warning'
            alertes_importantes.append(agent_info)
        else:
            agent_info['statut'] = 'ok'
            agent_info['classe_alerte'] = 'success'
            agents_ok.append(agent_info)
    
    total_agents = agents_centre.count()
    nb_critiques = len(alertes_critiques)
    nb_urgentes = len(alertes_urgentes)
    nb_importantes = len(alertes_importantes)
    nb_ok = len(agents_ok)
    
    context = {
        'centre': centre,
        'titre': f"Dashboard Médical - {centre.code_centre}",
        'alertes_critiques': alertes_critiques,
        'alertes_urgentes': alertes_urgentes,
        'alertes_importantes': alertes_importantes,
        'agents_ok': agents_ok,
        'stats': {
            'total': total_agents,
            'critiques': nb_critiques,
            'urgentes': nb_urgentes,
            'importantes': nb_importantes,
            'ok': nb_ok,
            'taux_conformite': round((nb_ok / total_agents * 100) if total_agents > 0 else 0, 1)
        }
    }
    
    return render(request, 'core/medical/dashboard_centre.html', context)


@login_required
def declarer_arret_maladie_view(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    
    # Vérif permissions : Chef Centre ou Adjoint Chef Centre UNIQUEMENT
    if not peut_gerer_arret_maladie(request, agent):
        raise PermissionDenied("Seul le Chef de Centre ou son Adjoint peut déclarer un arrêt maladie.")
    
    if request.method == 'POST':
        form = ArretMaladieForm(request.POST, request.FILES)
        if form.is_valid():
            arret = form.save(commit=False)
            arret.agent = agent
            # Par défaut, un nouvel arrêt est EN_COURS
            if hasattr(arret, 'statut'):
                arret.statut = 'EN_COURS'
            arret.save()
            
            if arret.est_long_terme:
                messages.warning(
                    request,
                    f"Arrêt maladie enregistré pour {agent.trigram}. "
                    f"Durée : {arret.duree_jours} jours (> 21j) → Visite de reprise obligatoire."
                )
            else:
                messages.success(
                    request,
                    f"Arrêt maladie enregistré pour {agent.trigram}. "
                    f"Durée : {arret.duree_jours} jours."
                )
            
            return redirect('dossier_medical', agent_id=agent.id_agent)
    else:
        form = ArretMaladieForm()
    
    context = {
        'form': form,
        'agent_concerne': agent,
        'titre': f"Déclarer un Arrêt Maladie - {agent.trigram}"
    }
    
    return render(request, 'core/medical/declarer_arret.html', context)


@login_required
def modifier_arret_maladie_view(request, arret_id):
    """
    Permet au Chef Centre/Adjoint de modifier un arrêt EN_COURS.
    Typiquement pour prolonger (changer date_fin_prevue).
    """
    arret = get_object_or_404(ArretMaladie, pk=arret_id)
    agent = arret.agent
    
    # Vérif permissions : Chef Centre ou Adjoint Chef Centre UNIQUEMENT
    if not peut_gerer_arret_maladie(request, agent):
        raise PermissionDenied("Seul le Chef de Centre ou son Adjoint peut modifier un arrêt maladie.")
    
    # Ne peut modifier que les arrêts EN_COURS
    if hasattr(arret, 'statut') and arret.statut != 'EN_COURS':
        messages.error(request, "Cet arrêt ne peut plus être modifié (déjà clôturé ou annulé).")
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    if request.method == 'POST':
        form = ArretMaladieForm(request.POST, request.FILES, instance=arret)
        if form.is_valid():
            arret = form.save()
            
            messages.success(
                request,
                f"Arrêt maladie modifié. Nouvelle date de fin prévue : {arret.date_fin_prevue.strftime('%d/%m/%Y')}."
            )
            
            # Alerte si proche du seuil PFU
            if arret.proche_seuil_pfu:
                messages.warning(
                    request,
                    f"⚠️ Attention : L'arrêt dure depuis {arret.jours_ecoules_depuis_debut} jours. "
                    f"PFU requis à 90 jours."
                )
            
            return redirect('dossier_medical', agent_id=agent.id_agent)
    else:
        form = ArretMaladieForm(instance=arret)
    
    context = {
        'form': form,
        'arret': arret,
        'agent_concerne': agent,
        'titre': f"Modifier Arrêt Maladie - {agent.trigram}",
        'action': 'modifier'
    }
    
    return render(request, 'core/medical/form_arret.html', context)


@login_required
def cloturer_arret_maladie_view(request, arret_id):
    """
    Permet au Chef Centre/Adjoint de déclarer la reprise de l'agent.
    Enregistre date_fin_reelle = aujourd'hui et statut = CLOTURE.
    """
    arret = get_object_or_404(ArretMaladie, pk=arret_id)
    agent = arret.agent
    
    # Vérif permissions
    if not peut_gerer_arret_maladie(request, agent):
        raise PermissionDenied("Seul le Chef de Centre ou son Adjoint peut clôturer un arrêt maladie.")
    
    # Ne peut clôturer que les arrêts EN_COURS
    if hasattr(arret, 'statut') and arret.statut != 'EN_COURS':
        messages.error(request, "Cet arrêt est déjà clôturé ou annulé.")
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    if request.method == 'POST':
        from django.utils import timezone
        from datetime import date
        
        arret.date_fin_reelle = date.today()
        if hasattr(arret, 'statut'):
            arret.statut = 'CLOTURE'
        if hasattr(arret, 'cloture_par'):
            arret.cloture_par = request.user
        if hasattr(arret, 'date_cloture'):
            arret.date_cloture = timezone.now()
        arret.save()
        
        messages.success(
            request,
            f"✅ Reprise de {agent.trigram} enregistrée. Arrêt clôturé."
        )
        
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    context = {
        'arret': arret,
        'agent_concerne': agent,
        'titre': f"Déclarer Reprise - {agent.trigram}"
    }
    
    return render(request, 'core/medical/cloturer_arret.html', context)


@login_required
def annuler_arret_maladie_view(request, arret_id):
    """
    Permet au Chef Centre/Adjoint d'annuler un arrêt (erreur de saisie).
    """
    arret = get_object_or_404(ArretMaladie, pk=arret_id)
    agent = arret.agent
    
    # Vérif permissions
    if not peut_gerer_arret_maladie(request, agent):
        raise PermissionDenied("Seul le Chef de Centre ou son Adjoint peut annuler un arrêt maladie.")
    
    # Ne peut annuler que les arrêts EN_COURS
    if hasattr(arret, 'statut') and arret.statut != 'EN_COURS':
        messages.error(request, "Cet arrêt est déjà clôturé ou annulé.")
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    if request.method == 'POST':
        if hasattr(arret, 'statut'):
            arret.statut = 'ANNULE'
        arret.save()
        
        messages.warning(
            request,
            f"Arrêt maladie annulé (erreur de saisie)."
        )
        
        return redirect('dossier_medical', agent_id=agent.id_agent)
    
    context = {
        'arret': arret,
        'agent_concerne': agent,
        'titre': f"Annuler Arrêt Maladie - {agent.trigram}"
    }
    
    return render(request, 'core/medical/annuler_arret.html', context)


# ============================================================================
# VUE NATIONALE - Dashboard Chef de Division
# ============================================================================

@login_required
def dashboard_medical_national_view(request):
    """
    Dashboard médical national pour le Chef de Division.
    Vue consolidée de tous les centres avec filtres.
    """
    # Vérification des permissions
    # 1. Chef de Division, Adjoint Chef de Division, ou Adjoint Form
    if request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_FORM
    ]:
        pass  # Accès autorisé
    # 2. Permission view_all_licences
    elif 'competences.view_all_licences' in request.effective_perms:
        pass  # Accès autorisé
    else:
        raise PermissionDenied("Accès réservé au Chef de Division, Adjoint Form ou Responsable Formation National.")
    
    agents_queryset = Agent.objects.filter(actif=True).select_related('centre')
    
    filtre_centre = request.GET.get('centre', '')
    filtre_statut = request.GET.get('statut', '')
    filtre_echeance = request.GET.get('echeance', '')
    
    if filtre_centre:
        agents_queryset = agents_queryset.filter(centre_id=filtre_centre)
    
    tous_agents = list(agents_queryset.order_by('centre__code_centre', 'trigram'))
    today = date.today()
    
    agents_par_statut = {'critiques': [], 'urgents': [], 'importants': [], 'ok': []}
    stats_par_centre = {}
    
    for agent_item in tous_agents:
        cert = agent_item.certificat_medical_actif()
        agent_info = {
            'agent': agent_item,
            'certificat': cert,
            'jours_restants': None,
            'statut': 'inconnu',
            'classe_alerte': 'secondary'
        }
        
        if agent_item.centre:
            centre_code = agent_item.centre.code_centre
            if centre_code not in stats_par_centre:
                stats_par_centre[centre_code] = {
                    'centre': agent_item.centre,
                    'total': 0,
                    'critiques': 0,
                    'urgents': 0,
                    'importants': 0,
                    'ok': 0
                }
            stats_par_centre[centre_code]['total'] += 1
        
        if not cert:
            agent_info['statut'] = 'aucun_certificat'
            agent_info['classe_alerte'] = 'danger'
            agents_par_statut['critiques'].append(agent_info)
            if agent_item.centre:
                stats_par_centre[centre_code]['critiques'] += 1
            continue
        
        if cert.resultat != 'APTE':
            agent_info['statut'] = 'inapte'
            agent_info['classe_alerte'] = 'danger'
            agents_par_statut['critiques'].append(agent_info)
            if agent_item.centre:
                stats_par_centre[centre_code]['critiques'] += 1
            continue
        
        if not cert.date_expiration_aptitude:
            agent_info['statut'] = 'pas_expiration'
            agent_info['classe_alerte'] = 'warning'
            agents_par_statut['urgents'].append(agent_info)
            if agent_item.centre:
                stats_par_centre[centre_code]['urgents'] += 1
            continue
        
        jours_restants = (cert.date_expiration_aptitude - today).days
        agent_info['jours_restants'] = jours_restants
        
        if jours_restants < 0:
            agent_info['statut'] = 'expire'
            agent_info['classe_alerte'] = 'danger'
            agents_par_statut['critiques'].append(agent_info)
            if agent_item.centre:
                stats_par_centre[centre_code]['critiques'] += 1
        elif jours_restants <= 30:
            agent_info['statut'] = 'expire_bientot'
            agent_info['classe_alerte'] = 'danger'
            agents_par_statut['urgents'].append(agent_info)
            if agent_item.centre:
                stats_par_centre[centre_code]['urgents'] += 1
        elif jours_restants <= 90:
            agent_info['statut'] = 'a_surveiller'
            agent_info['classe_alerte'] = 'warning'
            agents_par_statut['importants'].append(agent_info)
            if agent_item.centre:
                stats_par_centre[centre_code]['importants'] += 1
        else:
            agent_info['statut'] = 'ok'
            agent_info['classe_alerte'] = 'success'
            agents_par_statut['ok'].append(agent_info)
            if agent_item.centre:
                stats_par_centre[centre_code]['ok'] += 1
    
    agents_filtres = []
    if filtre_statut == 'critiques':
        agents_filtres = agents_par_statut['critiques']
    elif filtre_statut == 'urgents':
        agents_filtres = agents_par_statut['urgents']
    elif filtre_statut == 'importants':
        agents_filtres = agents_par_statut['importants']
    elif filtre_statut == 'ok':
        agents_filtres = agents_par_statut['ok']
    else:
        for liste in agents_par_statut.values():
            agents_filtres.extend(liste)
    
    if filtre_echeance == '30':
        agents_filtres = [a for a in agents_filtres if a['jours_restants'] is not None and a['jours_restants'] <= 30]
    elif filtre_echeance == '90':
        agents_filtres = [a for a in agents_filtres if a['jours_restants'] is not None and a['jours_restants'] <= 90]
    elif filtre_echeance == 'expire':
        agents_filtres = [a for a in agents_filtres if a['jours_restants'] is not None and a['jours_restants'] < 0]
    
    total_agents = len(tous_agents)
    nb_critiques = len(agents_par_statut['critiques'])
    nb_urgents = len(agents_par_statut['urgents'])
    nb_importants = len(agents_par_statut['importants'])
    nb_ok = len(agents_par_statut['ok'])
    
    for centre_stats in stats_par_centre.values():
        if centre_stats['total'] > 0:
            centre_stats['taux_conformite'] = round((centre_stats['ok'] / centre_stats['total']) * 100, 1)
        else:
            centre_stats['taux_conformite'] = 0
    
    stats_centres_tries = sorted(stats_par_centre.values(), key=lambda x: x['taux_conformite'])
    centres_disponibles = Centre.objects.all().order_by('code_centre')
    
    context = {
        'titre': 'Dashboard Médical National',
        'stats_globales': {
            'total': total_agents,
            'critiques': nb_critiques,
            'urgents': nb_urgents,
            'importants': nb_importants,
            'ok': nb_ok,
            'taux_conformite': round((nb_ok / total_agents * 100) if total_agents > 0 else 0, 1)
        },
        'stats_centres': stats_centres_tries,
        'agents_filtres': agents_filtres,
        'centres_disponibles': centres_disponibles,
        'filtre_centre': filtre_centre,
        'filtre_statut': filtre_statut,
        'filtre_echeance': filtre_echeance,
    }
    
    return render(request, 'core/medical/dashboard_national.html', context)
