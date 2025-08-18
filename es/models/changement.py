# Fichier : es/models/changemnt.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import Agent, Centre
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

# ==============================================================================
# 1. MODÈLE CHANGEMENT : LE DOSSIER ADMINISTRATIF
# ==============================================================================
class Changement(models.Model):
    class Classification(models.TextChoices):
        NON_DEFINI = 'NON_DEFINI', 'Non Défini'
        SUIVI = 'SUIVI', 'Suivi'
        NON_SUIVI = 'NON_SUIVI', 'Non Suivi'
    class StatutProcessus(models.TextChoices):
        NOTIFICATION = 'NOTIFICATION', 'En attente de classification'
        ETUDE_REQUISE = 'ETUDE_REQUISE', 'Étude de sécurité requise'
        REALISATION = 'REALISATION', 'Réalisation'
        CLOS = 'CLOS', 'Clos'
    titre = models.CharField(max_length=255, verbose_name="Titre / Objet du changement")
    description = models.TextField(verbose_name="Description sommaire du besoin")
    initiateur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='changements_inities', verbose_name="Initiateur (ES Local)")
    centre_principal = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='changements_pilotes', verbose_name="Centre pilote")
    fichier_notification_initiale = models.FileField(upload_to='es/notifications/%Y/%m/', verbose_name="Fichier de Notification (Annexe 1)")
    fichier_reponse_notification = models.FileField(upload_to='es/reponses/%Y/%m/', null=True, blank=True, verbose_name="Fichier de Réponse (Annexe 2)")
    classification = models.CharField(max_length=20, choices=Classification.choices, default=Classification.NON_DEFINI)
    correspondant_dircam = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='changements_supervises', verbose_name="Correspondant (ES National)")
    statut = models.CharField(max_length=20, choices=StatutProcessus.choices, default=StatutProcessus.NOTIFICATION)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Processus de Changement"
        verbose_name_plural = "Processus de Changements"
        ordering = ['-created_at']
    def __str__(self):
        return self.titre