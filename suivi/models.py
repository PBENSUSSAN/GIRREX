# Fichier : suivi/models.py

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from core.models import Agent, Centre

# --- QuerySet Personnalisé (définit la logique de filtrage) ---
class ActionQuerySet(models.QuerySet):
    def for_user(self, user):
        if not hasattr(user, 'agent_profile'):
            return self.none()
        agent = user.agent_profile
        if not agent.centre or user.is_superuser:
            return self.all()
        return self.filter(
            models.Q(centre__isnull=True) | models.Q(centre=agent.centre)
        )

# --- Managers Personnalisés (utilisent le QuerySet) ---
class ActionManager(models.Manager):
    def get_queryset(self):
        # Utilise le QuerySet et exclut les archives
        return ActionQuerySet(self.model, using=self._db).exclude(statut='ARCHIVEE')
    
    def for_user(self, user):
        # Raccourci pour appeler la méthode du QuerySet
        return self.get_queryset().for_user(user)

class ArchiveManager(models.Manager):
    def get_queryset(self):
        # Utilise le QuerySet mais N'exclut PAS les archives
        return ActionQuerySet(self.model, using=self._db)
    
    def for_user(self, user):
        # Raccourci pour appeler la méthode du QuerySet
        return self.get_queryset().for_user(user)

# --- Modèle Principal : Action ---
class Action(models.Model):
    class CategorieAction(models.TextChoices):
        FONCTIONNEMENT = 'FONCTIONNEMENT', 'Fonctionnement'
        DIFFUSION_DOC = 'DIFFUSION_DOC', 'Diffusion Documentaire'
        RECOMMANDATION_QS = 'RECOMMANDATION_QS', 'Recommandation QS'
        PRISE_EN_COMPTE_DOC = 'PRISE_EN_COMPTE_DOC', 'Prise en Compte Documentaire'
        AUDIT = 'AUDIT', 'Audit'
        ETUDE_SECURITE = 'ETUDE_SECURITE', 'Étude de Sécurité'
    
    class StatutAction(models.TextChoices):
        A_FAIRE = 'A_FAIRE', 'À faire'
        EN_COURS = 'EN_COURS', 'En cours'
        A_VALIDER = 'A_VALIDER', 'À valider'
        VALIDEE = 'VALIDEE', 'Validée / Clôturée'
        REFUSEE = 'REFUSEE', 'Refusée'
        ARCHIVEE = 'ARCHIVEE', 'Archivée'
    
    class Priorite(models.TextChoices):
        BASSE = 'BASSE', 'Basse'
        MOYENNE = 'MOYENNE', 'Moyenne'
        HAUTE = 'HAUTE', 'Haute'

    numero_action = models.CharField(max_length=50, unique=True, blank=True)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    categorie = models.CharField(max_length=30, choices=CategorieAction.choices, default=CategorieAction.FONCTIONNEMENT)
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, null=True, blank=True, related_name='actions_locales')
    responsable = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='actions_a_realiser')
    echeance = models.DateField()
    priorite = models.CharField(max_length=20, choices=Priorite.choices, default=Priorite.MOYENNE)
    statut = models.CharField(max_length=20, choices=StatutAction.choices, default=StatutAction.A_FAIRE)
    avancement = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sous_taches')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    objet_source = GenericForeignKey('content_type', 'object_id')
    echeance_proposee = models.DateField(null=True, blank=True)
    
    objects = ActionManager()
    archives = ArchiveManager()

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero_action:
            portee_code = "LOC" if self.centre else "NAT"
            categorie_prefix_map = {
                'FONCTIONNEMENT': 'FCT',
                'DIFFUSION_DOC': 'DOC',
                'RECOMMANDATION_QS': 'QS',
                'PRISE_EN_COMPTE_DOC': 'PEC',
                'AUDIT': 'AUD',
                'ETUDE_SECURITE': 'ES',
            }
            type_code = categorie_prefix_map.get(self.categorie, 'ACT')
            current_year = timezone.now().year
            prefix = f"{portee_code}-{type_code}-{current_year}-"
            
            last_action = Action.archives.filter(numero_action__startswith=prefix).order_by('numero_action').last()
            
            new_sequence = 1
            if last_action:
                last_sequence = int(last_action.numero_action.split('-')[-1])
                new_sequence = last_sequence + 1
            
            self.numero_action = f"{prefix}{new_sequence:04d}"
        
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['echeance', 'priorite']

    def __str__(self):
        return self.numero_action or str(self.id)

# --- Modèles de Support ---

class HistoriqueAction(models.Model):
    class TypeEvenement(models.TextChoices):
        CREATION = 'CREATION', 'Création'
        CHANGEMENT_STATUT = 'CHANGEMENT_STATUT', 'Changement de statut'
        CHANGEMENT_AVANCEMENT = 'CHANGEMENT_AVANCEMENT', 'Changement d\'avancement'
        COMMENTAIRE = 'COMMENTAIRE', 'Commentaire ajouté'
        DEMANDE_REAJUSTEMENT = 'DEMANDE_REAJUSTEMENT', 'Demande de réajustement d\'échéance'
        APPROBATION_REAJUSTEMENT = 'APPROBATION_REAJUSTEMENT', 'Approbation de réajustement'
        REFUS_REAJUSTEMENT = 'REFUS_REAJUSTEMENT', 'Refus de réajustement'
        CHANGEMENT_RESPONSABLE = 'CHANGEMENT_RESPONSABLE', 'Changement de responsable'
    
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='historique')
    type_evenement = models.CharField(max_length=30, choices=TypeEvenement.choices)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Auteur de l'événement")
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, help_text="Détails de l'événement au format JSON (ex: {'ancienne_valeur': 'EN_COURS', 'nouvelle_valeur': 'A_VALIDER'})")

    class Meta:
        verbose_name = "Historique d'Action"
        verbose_name_plural = "Historiques des Actions"
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.type_evenement} sur {self.action_id} par {self.auteur}"


class PriseEnCompte(models.Model):
    action_agent = models.OneToOneField(Action, on_delete=models.CASCADE, related_name='prise_en_compte')
    agent = models.ForeignKey('core.Agent', on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prise en compte de l'action #{self.action_agent.id} par {self.agent} le {self.timestamp.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Prise en compte par l'agent"
        verbose_name_plural = "Prises en compte par les agents"