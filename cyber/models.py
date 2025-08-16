# Fichier : cyber/models.py (Version Complète et Détaillée)

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from core.models import Agent, Centre
from documentation.models import Document
from technique.models import PanneCentre

# ==============================================================================
# 1. Le Dossier de Conformité SMSI (Pivot Central)
# ==============================================================================
class SMSI(models.Model):
    centre = models.OneToOneField(Centre, on_delete=models.PROTECT, related_name='smsi')
    relais_local = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='smsi_pilotes_locaux', help_text="Relais SMSI désigné pour ce centre (rôle SMSI_LOCAL).")
    manuel_management = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', help_text="Lien vers le Manuel de Management de la Sécurité de l'Information.")
    programme_surete = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', help_text="Lien vers le Programme de Sûreté.")
    
    class Meta:
        verbose_name = "Dossier de Conformité SMSI"
        verbose_name_plural = "Dossiers de Conformité SMSI"

    def __str__(self):
        return f"Dossier SMSI pour {self.centre.code_centre}"

# ==============================================================================
# 2. Le Registre des Risques Cyber
# Inspiré du §4.1 (Établissement du contexte) et §4.3 (Traitement des risques)
# ==============================================================================
class CyberRisque(models.Model):
    class Statut(models.TextChoices):
        OUVERT = 'OUVERT', 'Ouvert (en attente de traitement)'
        TRAITE = 'TRAITE', 'Traité (mesures appliquées)'
        ACCEPTE = 'ACCEPTE', 'Accepté (risque résiduel assumé)'
        REFUSE = 'REFUSE', 'Refusé (activité évitée)'

    class Gravite(models.TextChoices):
        FAIBLE = 'FAIBLE', 'Faible'
        MOYENNE = 'MOYENNE', 'Moyenne'
        ELEVEE = 'ELEVEE', 'Élevée'
        CRITIQUE = 'CRITIQUE', 'Critique'
        
    class Probabilite(models.TextChoices):
        TRES_FAIBLE = 'TRES_FAIBLE', 'Très Faible'
        FAIBLE = 'FAIBLE', 'Faible'
        MOYENNE = 'MOYENNE', 'Moyenne'
        ELEVEE = 'ELEVEE', 'Élevée'

    smsi = models.ForeignKey(SMSI, on_delete=models.CASCADE, related_name='risques')
    description = models.TextField(verbose_name="Description du risque")
    gravite = models.CharField(max_length=20, choices=Gravite.choices, default=Gravite.MOYENNE)
    probabilite = models.CharField(max_length=20, choices=Probabilite.choices, default=Probabilite.MOYENNE)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT)
    actions = GenericRelation('suivi.Action', related_query_name='cyber_risque')

    class Meta:
        verbose_name = "Risque de Cybersécurité"
        verbose_name_plural = "Registre des Risques de Cybersécurité"
        ordering = ['statut', '-gravite']

    def __str__(self):
        return f"Risque #{self.id} pour {self.smsi.centre.code_centre}"
    
    def get_absolute_url(self):
        """ Retourne l'URL pour la page de détail de cet objet. """
        return reverse('cyber:detail-risque', kwargs={'risque_id': self.pk})

# ==============================================================================
# 3. Le Registre des Incidents Cyber
# Inspiré du §4.4 (Gestion des incidents)
# ==============================================================================
class CyberIncident(models.Model):
    class Statut(models.TextChoices):
        DETECTION = 'DETECTION', 'Détection (en attente de qualification)'
        ANALYSE = 'ANALYSE', 'Analyse en cours'
        REMEDIATION = 'REMEDIATION', 'Remédiation en cours'
        RESOLU = 'RESOLU', 'Résolu'
        CLOTURE = 'CLOTURE', 'Clôturé (retour d\'expérience effectué)'

    smsi = models.ForeignKey(SMSI, on_delete=models.CASCADE, related_name='incidents')
    date = models.DateTimeField(default=timezone.now, verbose_name="Date et heure de l'incident")
    description = models.TextField(verbose_name="Description de l'incident")
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.DETECTION)
    source_panne = models.ForeignKey(PanneCentre, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents_cyber_associes', help_text="Lien vers la panne technique d'origine, si applicable.")
    actions = GenericRelation('suivi.Action', related_query_name='cyber_incident')

    class Meta:
        verbose_name = "Incident de Cybersécurité"
        verbose_name_plural = "Registre des Incidents de Cybersécurité"
        ordering = ['-date']

    def __str__(self):
        return f"Incident du {self.date.strftime('%d/%m/%Y')} sur {self.smsi.centre.code_centre}"
    
    def get_absolute_url(self):
        """ Retourne l'URL pour la page de détail de cet objet. """
        return reverse('cyber:detail-incident', kwargs={'incident_id': self.pk})

# ==============================================================================
# 4. Historique Permanent des Risques Cyber
# ==============================================================================
class CyberRisqueHistorique(models.Model):
    class TypeEvenement(models.TextChoices):
        CREATION = 'CREATION', 'Création du risque'
        CHANGEMENT_STATUT = 'CHANGEMENT_STATUT', 'Changement de statut'
        MODIFICATION = 'MODIFICATION', 'Modification des détails'
        COMMENTAIRE = 'COMMENTAIRE', 'Commentaire ajouté'

    risque = models.ForeignKey(CyberRisque, on_delete=models.CASCADE, related_name='historique')
    type_evenement = models.CharField(max_length=30, choices=TypeEvenement.choices)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Historique de Risque Cyber"
        ordering = ['-timestamp']

# ==============================================================================
# 5. Historique Permanent des Incidents Cyber
# ==============================================================================
class CyberIncidentHistorique(models.Model):
    class TypeEvenement(models.TextChoices):
        CREATION = 'CREATION', 'Création de l\'incident'
        CHANGEMENT_STATUT = 'CHANGEMENT_STATUT', 'Changement de statut'
        QUALIFICATION = 'QUALIFICATION', 'Qualification depuis une panne'
        COMMENTAIRE = 'COMMENTAIRE', 'Commentaire ajouté'
        RESOLUTION = 'RESOLUTION', 'Incident résolu'
        

    incident = models.ForeignKey(CyberIncident, on_delete=models.CASCADE, related_name='historique')
    type_evenement = models.CharField(max_length=30, choices=TypeEvenement.choices)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Historique d'Incident Cyber"
        ordering = ['-timestamp']

# ==============================================================================
# 6. Modèle Générique pour les Pièces Jointes
# ==============================================================================
class PieceJointe(models.Model):
    fichier = models.FileField(upload_to='cyber/pieces_jointes/%Y/%m/')
    description = models.CharField(max_length=255, blank=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Champs pour la relation générique
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Pièce Jointe"
        verbose_name_plural = "Pièces Jointes"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.fichier.name.split('/')[-1] # Affiche juste le nom du fichier