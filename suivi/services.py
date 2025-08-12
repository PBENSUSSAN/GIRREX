# Fichier : suivi/services.py

from django.utils import timezone
from datetime import timedelta
from .models import Action, HistoriqueAction
from core.models import Agent, Role, Centre
from documentation.models import Document
from qs.models import RecommendationQS 

def update_parent_progress(action_fille):
    """
    Met à jour l'avancement de l'action parente.
    """
    parent = action_fille.parent
    if not parent:
        return

    parent.refresh_from_db()
    filles = parent.sous_taches.all()
    total_filles = filles.count()
    
    if total_filles == 0:
        parent.avancement = 100
        parent.statut = Action.StatutAction.VALIDEE
        parent.save()
        return

    filles_validees = filles.filter(statut=Action.StatutAction.VALIDEE).count()
    pourcentage = int((filles_validees / total_filles) * 100)

    if pourcentage == 100:
        parent.avancement = 99
        parent.statut = Action.StatutAction.A_VALIDER
    else:
        parent.avancement = pourcentage
        if parent.statut == Action.StatutAction.A_VALIDER:
             parent.statut = Action.StatutAction.EN_COURS
    
    parent.save()

def final_close_action_cascade(action, user):
    """
    Passe une action à 100% et propage cette clôture à toutes ses sous-tâches.
    """
    if action.avancement < 100:
        ancien_statut_display = action.get_statut_display()
        action.avancement = 100
        action.statut = Action.StatutAction.VALIDEE
        action.save()
        HistoriqueAction.objects.create(
            action=action,
            type_evenement=HistoriqueAction.TypeEvenement.CHANGEMENT_STATUT,
            auteur=user,
            details={'ancien': ancien_statut_display, 'nouveau': "Validée (Clôture Finale)"}
        )

    for sous_tache in action.sous_taches.exclude(avancement=100):
        final_close_action_cascade(sous_tache, user)

def creer_diffusion(objet_source, initiateur, form_data):
    """
    Service centralisé et flexible qui gère tous les scénarios de diffusion.
    """
    type_diffusion = form_data['type_diffusion']
    # --- LOGIQUE SIMPLIFIÉE ---
    # La variable `centres_a_traiter` reçoit directement la liste du formulaire.
    # Plus besoin de deviner si c'est une diffusion nationale.
    centres_a_traiter = form_data['centres_cibles']
    agents_specifiques = form_data['agents_cibles']
    diffusion_directe = form_data['diffusion_directe_agents']
    
    tous_les_centres_cibles = Centre.objects.filter(pk__in=[c.pk for c in centres_a_traiter])
    portee_code = "LOC" if tous_les_centres_cibles.exists() or agents_specifiques.exists() else "NAT"
    categorie_action_mere = Action.CategorieAction.DIFFUSION_DOC
    
    prefix = f"{portee_code}-{categorie_action_mere.name.split('_')[0]}-{timezone.now().year}-"
    last_action = Action.archives.filter(
        numero_action__startswith=prefix,
        parent__isnull=True
    ).order_by('numero_action').last()
    
    new_sequence = 1
    if last_action and last_action.numero_action.split('-')[-1].isdigit():
        new_sequence = int(last_action.numero_action.split('-')[-1]) + 1
    
    numero_mere = f"{prefix}{new_sequence:04d}"

    action_mere = Action.objects.create(
        numero_action=numero_mere,
        titre=f"Diffusion de : {objet_source}",
        responsable=initiateur,
        echeance=timezone.now().date() + timedelta(days=14),
        objet_source=objet_source,
        categorie=categorie_action_mere,
        statut=Action.StatutAction.EN_COURS
    )
    if tous_les_centres_cibles.exists():
        action_mere.centres.set(tous_les_centres_cibles)

    destinataires_finaux = set(agents_specifiques)
    
    # La condition est simple : s'il y a des centres à traiter, on entre dans la logique.
    if centres_a_traiter.exists():
        if diffusion_directe:
            agents_concernes = Agent.objects.filter(
                centre__in=centres_a_traiter,
                actif=True
            ).distinct()
            destinataires_finaux.update(agents_concernes)
        else:
            ROLE_MAPPING = {
                Document: Role.RoleName.SMS_LOCAL,
                RecommendationQS: Role.RoleName.QS_LOCAL,
            }
            objet_type = type(objet_source)
            role_cible = ROLE_MAPPING.get(objet_type)

            for centre in centres_a_traiter:
                responsable_a_assigner = None
                if role_cible:
                    responsable_a_assigner = Agent.objects.filter(
                        roles_assignes__centre=centre,
                        roles_assignes__role__nom=role_cible,
                        roles_assignes__date_fin__isnull=True,
                        actif=True
                    ).first()
                
                if not responsable_a_assigner:
                    responsable_a_assigner = Agent.objects.filter(
                        roles_assignes__centre=centre,
                        roles_assignes__role__nom=Role.RoleName.CHEF_DE_CENTRE,
                        roles_assignes__date_fin__isnull=True,
                        actif=True
                    ).first()
                    if not responsable_a_assigner:
                        responsable_a_assigner = Agent.objects.filter(
                            roles_assignes__centre=centre,
                            roles_assignes__role__nom=Role.RoleName.ADJOINT_CHEF_DE_CENTRE,
                            roles_assignes__date_fin__isnull=True,
                            actif=True
                        ).first()

                if responsable_a_assigner:
                    numero_intermediaire = f"{numero_mere}.{centre.code_centre}"
                    
                    action_intermediaire = Action.objects.create(
                        parent=action_mere,
                        numero_action=numero_intermediaire,
                        titre=f"Dispatcher la diffusion de : {objet_source}",
                        responsable=responsable_a_assigner,
                        echeance=action_mere.echeance,
                        objet_source=objet_source,
                        categorie=categorie_action_mere
                    )
                    action_intermediaire.centres.set([centre])

    # Le reste de la fonction est inchangé
    index_depart = action_mere.sous_taches.filter(numero_action__contains='.').count()
    for i, agent in enumerate(destinataires_finaux):
        numero_final = f"{numero_mere}.{index_depart + i + 1}"
        Action.objects.create(
            parent=action_mere,
            numero_action=numero_final,
            titre=f"Prise en compte : {objet_source}",
            responsable=agent,
            echeance=action_mere.echeance,
            objet_source=objet_source,
            categorie=Action.CategorieAction.PRISE_EN_COMPTE_DOC
        )
        
    if type_diffusion == 'INFO' or not (action_mere.sous_taches.exists() or destinataires_finaux):
        action_mere.avancement = 100
        action_mere.statut = Action.StatutAction.VALIDEE
    else:
        action_mere.avancement = 1
    action_mere.save()
    
    return action_mere