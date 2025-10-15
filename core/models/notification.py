# Fichier : core/models/notification.py
from django.db import models
from django.utils import timezone
from .rh import Agent

class Notification(models.Model):
    """
    Système de notifications pour les agents.
    """
    
    class TypeNotification(models.TextChoices):
        INFO = 'INFO', 'Information'
        WARNING = 'WARNING', 'Avertissement'
        ALERT = 'ALERT', 'Alerte'
        SUCCESS = 'SUCCESS', 'Succès'
    
    destinataire = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire"
    )
    
    type_notification = models.CharField(
        max_length=20,
        choices=TypeNotification.choices,
        default=TypeNotification.INFO
    )
    
    titre = models.CharField(max_length=255)
    message = models.TextField()
    
    lue = models.BooleanField(
        default=False,
        verbose_name="Notification lue"
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_lecture = models.DateTimeField(null=True, blank=True)
    
    # Lien optionnel vers un objet
    lien_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="URL de redirection"
    )
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['destinataire', '-date_creation']),
            models.Index(fields=['destinataire', 'lue']),
        ]
    
    def __str__(self):
        return f"{self.titre} pour {self.destinataire}"
    
    def marquer_comme_lue(self):
        """Marque la notification comme lue."""
        if not self.lue:
            self.lue = True
            self.date_lecture = timezone.now()
            self.save()
