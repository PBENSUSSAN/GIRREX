# Fichier : suivi/services.py (Version Corrigée et Finalisée)

from django.utils import timezone
from datetime import timedelta
from .models import Action, HistoriqueAction
from core.models import Agent, Role, Centre
from documentation.models import Document
from qs.models import RecommendationQS 


def generer_numero_action(categorie, centre=None):
    """
    Génère un numéro d'action unique et standardisé en fonction de sa catégorie métier.
    Ex: QS-AIX-2025-0001 ou NAT-DIFFUSION-2025-0002
    """
    prefix_metier = ""
    
    # On détermine le préfixe métier en fonction de la catégorie
    if categorie in [Action.CategorieAction.INSTRUCTION_FNE, Action.CategorieAction.RECOMMANDATION_QS]:
        prefix_metier = "QS"
    elif categorie == Action.CategorieAction.ETUDE_SECURITE:
        prefix_metier = "ES"
    else: # Pour les autres cas (diffusion doc, etc.)
        prefix_metier = categorie.name.split('_')[0]
    
    # On détermine le préfixe de portée (centre ou national)
    portee_code = centre.code_centre if centre else "NAT"

    # Construction du préfixe final
    prefix = f"{prefix_metier}-{portee_code}-{timezone.now().year}-"
    
    # Recherche du dernier numéro
    last_action = Action.archives.filter(
        numero_action__startswith=prefix,
        parent__isnull=True
    ).order_by('numero_action').last()
    
    new_sequence = 1
    if last_action and last_action.numero_action.split('-')[-1].isdigit():
        new_sequence = int(last_action.numero_action.split('-')[-1]) + 1
        
    return f"{prefix}{new_sequence:04d}"


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
    centres_a_traiter = form_data['centres_cibles']
    agents_specifiques = form_data['agents_cibles']
    diffusion_directe = form_data['diffusion_directe_agents']
    
    tous_les_centres_cibles = Centre.objects.filter(pk__in=[c.pk for c in centres_a_traiter])
    
    # La catégorie dépend du type d'objet source
    if isinstance(objet_source, Document):
        categorie_action_mere = Action.CategorieAction.DIFFUSION_DOC
    elif isinstance(objet_source, RecommendationQS):
        categorie_action_mere = Action.CategorieAction.RECOMMANDATION_QS
    else:
        categorie_action_mere = Action.CategorieAction.FONCTIONNEMENT
    
    # --- ON UTILISE LA NOUVELLE FONCTION DE NUMÉROTATION ---
    # On passe None pour le centre car la logique de portée (LOC/NAT) n'est pas pertinente ici.
    # La fonction déterminera la portée en fonction de l'existence de centres.
    numero_mere = generer_numero_action(
        categorie=categorie_action_mere,
        centre=tous_les_centres_cibles.first() if tous_les_centres_cibles.count() == 1 else None
    )

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
    
    if centres_a_traiter: # .exists() n'est pas nécessaire sur un QuerySet dans un if
        if diffusion_directe:
            agents_concernes = Agent.objects.filter(
                centre__in=centres_a_traiter,
                actif=True
            ).distinct()
            destinataires_finaux.update(agents_concernes)
        else:
            # Logique pour trouver les responsables locaux (Chef de Centre, QS Local, etc.)
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
                    # Logique de fallback vers Chef de Centre / Adjoint
                    responsable_a_assigner = Agent.objects.filter(
                        roles_assignes__centre=centre,
                        roles_assignes__role__nom__in=[Role.RoleName.CHEF_DE_CENTRE, Role.RoleName.ADJOINT_CHEF_DE_CENTRE],
                        roles_assignes__date_fin__isnull=True,
                        actif=True
                    ).order_by('roles_assignes__role__nom').first()

                if responsable_a_assigner:
                    numero_intermediaire = f"{numero_mere}.{centre.code_centre}"
                    Action.objects.create(
                        parent=action_mere,
                        numero_action=numero_intermediaire,
                        titre=f"Dispatcher la diffusion de : {objet_source}",
                        responsable=responsable_a_assigner,
                        echeance=action_mere.echeance,
                        objet_source=objet_source,
                        categorie=categorie_action_mere
                    )

    # Création des sous-tâches pour les destinataires finaux
    index_depart = action_mere.sous_taches.count()
    for i, agent in enumerate(destinataires_finaux):
        numero_final = f"{numero_mere}.{index_depart + i + 1}"
        Action.objects.create(
            parent=action_mere,
            numero_action=numero_final,
            titre=f"Prise en compte : {objet_source}",
            responsable=agent,
            echeance=action_mere.echeance,
            objet_source=objet_source,
            # La catégorie de la sous-tâche peut être plus spécifique
            categorie=Action.CategorieAction.PRISE_EN_COMPTE_DOC if isinstance(objet_source, Document) else categorie_action_mere
        )
        
    if type_diffusion == 'INFO' or not (action_mere.sous_taches.exists() or destinataires_finaux):
        action_mere.avancement = 100
        action_mere.statut = Action.StatutAction.VALIDEE
    else:
        action_mere.avancement = 1
    action_mere.save()
    
    return action_mere