# Fichier : feedback/services.py

from django.utils import timezone
from datetime import timedelta
from .models import Feedback
from suivi.models import Action
from suivi.services import generer_numero_action
from core.models import Agent

def creer_feedback_et_action_suivi(form_data, auteur_agent):
    """
    Crée l'objet Feedback et l'action de suivi associée.
    C'est le SEUL endroit où 'feedback' interagit avec 'suivi'.
    """
    feedback = Feedback.objects.create(
        titre=form_data['titre'],
        description=form_data['description'],
        categorie=form_data['categorie'],
        module_concerne=form_data['module_concerne'],
        auteur=auteur_agent
    )

    # Assigne par défaut l'action à un super-utilisateur (admin)
    responsable_par_defaut = Agent.objects.filter(user__is_superuser=True).first()
    if not responsable_par_defaut:
        raise ValueError("Aucun Agent lié à un compte super-utilisateur n'a été trouvé pour prendre en charge le feedback.")

    numero_action = generer_numero_action(categorie=Action.CategorieAction.TRAITEMENT_FEEDBACK)
    
    action = Action.objects.create(
        numero_action=numero_action,
        titre=f"Feedback: {feedback.titre}",
        description=f"Demande de l'utilisateur {auteur_agent}:\n\n{feedback.description}",
        responsable=responsable_par_defaut,
        echeance=timezone.now().date() + timedelta(days=14),
        categorie=Action.CategorieAction.TRAITEMENT_FEEDBACK,
        objet_source=feedback
    )
    
    return feedback, action