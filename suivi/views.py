# Fichier : suivi/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Action

@login_required
def tableau_actions_view(request):
    """
    Affiche le "Tableau d'Actions Unique".
    La logique de filtrage est maintenant déléguée au manager du modèle.
    """
    # ==============================================================================
    # MODIFICATION : L'appel à la base de données est maintenant beaucoup plus simple
    # ==============================================================================
    # Ancien code :
    # actions_list = Action.objects.all().order_by('echeance')
    
    # Nouveau code :
    # On utilise notre nouvelle méthode "intelligente" for_user()
    actions_list = Action.objects.for_user(request.user).order_by('echeance')
    # ==============================================================================

    context = {
        'actions': actions_list,
        'titre': "Tableau de Suivi des Actions"
    }
    
    return render(request, 'suivi/tableau_actions.html', context)