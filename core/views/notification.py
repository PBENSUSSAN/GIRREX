# Fichier : core/views/notification.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from ..models import Notification

@login_required
def liste_notifications(request):
    """
    Affiche la liste des notifications de l'utilisateur connecté.
    """
    if not hasattr(request.user, 'agent_profile'):
        return redirect('home')
    
    agent = request.user.agent_profile
    
    # Récupérer les notifications
    notifications_non_lues = Notification.objects.filter(
        destinataire=agent,
        lue=False
    )
    
    notifications_lues = Notification.objects.filter(
        destinataire=agent,
        lue=True
    )[:20]  # Les 20 dernières lues
    
    context = {
        'notifications_non_lues': notifications_non_lues,
        'notifications_lues': notifications_lues,
        'nb_non_lues': notifications_non_lues.count(),
    }
    
    return render(request, 'core/notifications.html', context)


@login_required
def marquer_notification_lue(request, notification_id):
    """
    Marque une notification comme lue.
    """
    if not hasattr(request.user, 'agent_profile'):
        return JsonResponse({'error': 'Agent profile not found'}, status=403)
    
    agent = request.user.agent_profile
    
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        destinataire=agent
    )
    
    notification.marquer_comme_lue()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Requête AJAX
        return JsonResponse({
            'success': True,
            'message': 'Notification marquée comme lue'
        })
    
    # Redirection normale
    return redirect('liste-notifications')


@login_required
def marquer_toutes_lues(request):
    """
    Marque toutes les notifications comme lues.
    """
    if not hasattr(request.user, 'agent_profile'):
        return JsonResponse({'error': 'Agent profile not found'}, status=403)
    
    agent = request.user.agent_profile
    
    notifications = Notification.objects.filter(
        destinataire=agent,
        lue=False
    )
    
    for notif in notifications:
        notif.marquer_comme_lue()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{notifications.count()} notifications marquées comme lues'
        })
    
    return redirect('liste-notifications')


@login_required
def nombre_notifications_non_lues(request):
    """
    API pour récupérer le nombre de notifications non lues (pour le badge).
    """
    if not hasattr(request.user, 'agent_profile'):
        return JsonResponse({'count': 0})
    
    agent = request.user.agent_profile
    count = Notification.objects.filter(
        destinataire=agent,
        lue=False
    ).count()
    
    return JsonResponse({'count': count})
