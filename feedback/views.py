# Fichier : feedback/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Feedback
from .forms import FeedbackForm
from .services import creer_feedback_et_action_suivi
from core.decorators import effective_permission_required

@login_required
def soumettre_feedback_view(request):
    if not hasattr(request.user, 'agent_profile'):
        messages.error(request, "Votre compte n'est pas lié à un profil agent.")
        return redirect('home')

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            try:
                creer_feedback_et_action_suivi(form.cleaned_data, request.user.agent_profile)
                messages.success(request, "Votre retour a bien été envoyé. Merci pour votre contribution !")
                return redirect('home')
            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {e}")
    else:
        form = FeedbackForm()

    context = {
        'form': form,
        'titre': "Soumettre une demande ou une remarque"
    }
    return render(request, 'feedback/soumettre_feedback.html', context)

@login_required
@effective_permission_required('feedback.view_feedback_dashboard')
def liste_feedback_view(request):
    feedback_list = Feedback.objects.select_related('auteur').prefetch_related('action_suivi').all()
    context = {
        'feedback_list': feedback_list,
        'titre': "Tableau de Bord des Retours Utilisateurs"
    }
    return render(request, 'feedback/liste_feedback.html', context)

@login_required
@effective_permission_required('feedback.view_feedback_dashboard')
def detail_feedback_view(request, feedback_id):
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    action_suivi = feedback.action_suivi.first() # Récupère la première (et unique) action liée
    
    context = {
        'feedback': feedback,
        'action_suivi': action_suivi,
        'titre': f"Détail du Feedback #{feedback.id}"
    }
    return render(request, 'feedback/detail_feedback.html', context)