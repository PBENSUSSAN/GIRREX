# Fichier : qs/services.py

from django.utils import timezone
from datetime import timedelta

from .models import DossierEvenement, FNE
from core.models import Agent, Centre, Role # On importe le modèle Role pour accéder aux noms
from suivi.models import Action

def creer_processus_fne_depuis_pre_declaration(agent_implique, description, centre, createur):
    """
    Service qui orchestre la création d'un Dossier, d'une FNE et des 
    deux actions de suivi initiales suite à une pré-déclaration.
    """
    
    now = timezone.now()
    id_girrex = f"GIRREX-EVT-{now.strftime('%Y%m%d-%H%M%S')}"
    
    dossier = DossierEvenement.objects.create(
        id_girrex=id_girrex,
        titre=f"Événement signalé à {centre.code_centre} le {now.strftime('%d/%m/%Y')}",
        date_evenement=now.date()
    )

    fne = FNE.objects.create(
        dossier=dossier,
        centre=centre,
        agent_implique=agent_implique
    )
    
    # --- DÉBUT DE LA LOGIQUE CORRIGÉE ---
    
    # 1. On cherche d'abord le responsable métier, le QS_LOCAL
    responsable_instruction = Agent.objects.filter(
        roles_assignes__centre=centre,
        roles_assignes__role__nom=Role.RoleName.QS_LOCAL,
        roles_assignes__date_fin__isnull=True,
        actif=True
    ).first()
    
    # 2. Si on ne le trouve pas, on cherche le responsable hiérarchique (Chef de Centre)
    if not responsable_instruction:
        responsable_instruction = Agent.objects.filter(
            roles_assignes__centre=centre,
            roles_assignes__role__nom=Role.RoleName.CHEF_DE_CENTRE,
            roles_assignes__date_fin__isnull=True,
            actif=True
        ).first()

    # 3. En dernier recours, on cherche un Adjoint
    if not responsable_instruction:
        responsable_instruction = Agent.objects.filter(
            roles_assignes__centre=centre,
            roles_assignes__role__nom=Role.RoleName.ADJOINT_CHEF_DE_CENTRE,
            roles_assignes__date_fin__isnull=True,
            actif=True
        ).first()
        
    # 4. Vérification finale : si personne n'est trouvé, on lève une erreur claire.
    if not responsable_instruction:
        raise ValueError(f"Impossible de créer le processus FNE : aucun responsable (QS Local, Chef ou Adjoint) n'est défini pour le centre {centre.code_centre}.")

    # --- FIN DE LA LOGIQUE CORRIGÉE ---
    
    action_cloture = Action.objects.create(
        titre=f"Instruire et clôturer FNE (OASIS: en attente)",
        responsable=responsable_instruction, # On utilise notre variable qui est garantie de ne pas être vide
        echeance=now.date() + timedelta(days=87),
        categorie=Action.CategorieAction.ETUDE_SECURITE,
        objet_source=fne,
        statut=Action.StatutAction.A_FAIRE
    )
    action_cloture.centres.set([centre])
    
    Action.objects.create(
        parent=action_cloture,
        titre=f"Déclarer l'événement dans OASIS",
        description=description,
        responsable=agent_implique,
        echeance=now.date() + timedelta(days=3),
        categorie=Action.CategorieAction.ETUDE_SECURITE,
        objet_source=fne
    )
    
    return fne