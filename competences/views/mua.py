# Fichier : competences/views/mua.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
# On importe notre nouveau service
from .. import services
from ..models import MentionUniteAnnuelle

@login_required
def dossier_mua_view(request, mua_id):
    """
    Affiche le dossier de suivi/renouvellement pour une MUA spécifique.
    Cette vue est maintenant "mince" : elle délègue toute la logique
    au service `get_mua_dossier_context`.
    """
    mua = get_object_or_404(
        MentionUniteAnnuelle.objects.select_related('qualification__brevet__agent', 'qualification__centre'),
        pk=mua_id
    )
    
    # Appel du service pour obtenir toutes les données calculées
    context_data = services.get_mua_dossier_context(mua)
    
    # Préparation du contexte final pour le template
    context = {
        'mua': mua,
        'agent_concerne': mua.qualification.brevet.agent,
        'centre': mua.qualification.centre, # Ajouté pour le template du relevé mensuel
        'titre': f"Dossier de suivi MUA {mua.get_type_flux_display()} pour {mua.qualification.brevet.agent.trigram}",
        # On dépaquette le dictionnaire retourné par le service directement dans le contexte
        **context_data 
    }
    
    return render(request, 'competences/dossier_mua.html', context)

@login_required
def releve_mensuel_view(request, mua_id):
    """
    Affiche la page dédiée au relevé mensuel détaillé des heures pour une MUA.
    """
    mua = get_object_or_404(
        MentionUniteAnnuelle.objects.select_related('qualification__brevet__agent', 'qualification__centre'),
        pk=mua_id
    )
    
    # On appelle le service pour obtenir les données déjà calculées
    context_data = services.get_mua_dossier_context(mua)

    context = {
        'mua': mua,
        'agent_concerne': mua.qualification.brevet.agent,
        'centre': mua.qualification.centre,
        'titre': f"Relevé Mensuel pour {mua.qualification.brevet.agent.nom}",
    }
    context.update(context_data)
    return render(request, 'competences/releve_mensuel.html', context)
    