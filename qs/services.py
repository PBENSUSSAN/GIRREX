# Fichier : qs/services.py

from django.utils import timezone
from datetime import timedelta

from .models import FNE  # On importe seulement FNE maintenant
from core.models import Agent, Centre, Role
from suivi.models import Action
from suivi.services import generer_numero_action

def creer_processus_fne_depuis_pre_declaration(agent_implique, description, centre, createur):
    """
    Service qui orchestre la création d'une FNE unique et des 
    deux actions de suivi initiales suite à une pré-déclaration.
    """
    
    now = timezone.now()
    # On génère l'ID Girrex pour la FNE elle-même
    id_girrex = f"GIRREX-EVT-{now.strftime('%Y%m%d-%H%M%S')}"
    
    # On crée directement la FNE avec toutes les informations nécessaires
    fne = FNE.objects.create(
        # Champs anciennement dans DossierEvenement
        id_girrex=id_girrex,
        titre=f"Événement signalé à {centre.code_centre} le {now.strftime('%d/%m/%Y')}",
        date_evenement=now.date(),
        
        # Champs propres à la FNE
        centre=centre,
        agent_implique=agent_implique
        # Le statut par défaut est déjà 'PRE_DECLAREE'
    )
    
    # La logique de recherche du responsable reste la même
    responsable_instruction = Agent.objects.filter(
        roles_assignes__centre=centre,
        roles_assignes__role__nom=Role.RoleName.QS_LOCAL,
        roles_assignes__date_fin__isnull=True,
        actif=True
    ).first()
    
    if not responsable_instruction:
        responsable_instruction = Agent.objects.filter(
            roles_assignes__centre=centre,
            roles_assignes__role__nom=Role.RoleName.CHEF_DE_CENTRE,
            roles_assignes__date_fin__isnull=True,
            actif=True
        ).first()

    if not responsable_instruction:
        responsable_instruction = Agent.objects.filter(
            roles_assignes__centre=centre,
            roles_assignes__role__nom=Role.RoleName.ADJOINT_CHEF_DE_CENTRE,
            roles_assignes__date_fin__isnull=True,
            actif=True
        ).first()
        
    if not responsable_instruction:
        raise ValueError(f"Impossible de créer le processus FNE : aucun responsable (QS Local, Chef ou Adjoint) n'est défini pour le centre {centre.code_centre}.")

    categorie_action_fne = Action.CategorieAction.INSTRUCTION_FNE
    
    numero_action_mere = generer_numero_action(
        categorie=categorie_action_fne,
        centre=centre
    )

    action_cloture = Action.objects.create(
        numero_action=numero_action_mere,
        titre=f"Instruire et clôturer FNE ({numero_action_mere})",
        responsable=responsable_instruction,
        echeance=now.date() + timedelta(days=87),
        categorie=categorie_action_fne,
        objet_source=fne,
        statut=Action.StatutAction.A_FAIRE
    )
    action_cloture.centres.set([centre])
    
    Action.objects.create(
        parent=action_cloture,
        numero_action=f"{numero_action_mere}.1",
        titre=f"Déclarer l'événement dans OASIS",
        description=description,
        responsable=agent_implique,
        echeance=now.date() + timedelta(days=3),
        categorie=categorie_action_fne,
        objet_source=fne
    )
    
    return fne