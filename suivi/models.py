# Fichier : suivi/models.py (Version avec Correction de l'Avancement à 100%)

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from core.models import Agent, Centre

# ==============================================================================
# QUERYSET ET MANAGERS
# ==============================================================================
class ActionQuerySet(models.QuerySet):
    def for_user(self, user):
        if not hasattr(user, 'agent_profile'):
            return self.none()
        agent = user.agent_profile
        if user.is_superuser:
            return self.all()
        
        q_responsable = models.Q(responsable=agent)
        q_responsable_parent = models.Q(parent__responsable=agent)
        q_a_une_sous_tache_assignee = models.Q(sous_taches__responsable=agent)
        
        final_query = q_responsable | q_responsable_parent | q_a_une_sous_tache_assignee
        
        return self.filter(final_query).distinct()

class ActionManager(models.Manager):
    def get_queryset(self):
        return ActionQuerySet(self.model, using=self._db).exclude(statut='ARCHIVEE')
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)

class ArchiveManager(models.Manager):
    def get_queryset(self):
        return ActionQuerySet(self.model, using=self._db)
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)

# ==============================================================================
# MODÈLE PRINCIPAL : ACTION
# ==============================================================================
class Action(models.Model):
    class CategorieAction(models.TextChoices):
        FONCTIONNEMENT = 'FONCTIONNEMENT', 'Fonctionnement'
        DIFFUSION_DOC = 'DIFFUSION_DOC', 'Diffusion Documentaire'
        RECOMMANDATION_QS = 'RECOMMANDATION_QS', 'Recommandation QS'
        PRISE_EN_COMPTE_DOC = 'PRISE_EN_COMPTE_DOC', 'Prise en Compte Documentaire'
        AUDIT = 'AUDIT', 'Audit'
        ETUDE_SECURITE = 'ETUDE_SECURITE', 'Étude de Sécurité'
        INSTRUCTION_FNE = 'INSTRUCTION_FNE', 'Instruction FNE (QS)'
        # --- NOUVELLES CATÉGORIES ---
        RELECTURE_DOC = 'RELECTURE_DOC', 'Relecture Documentaire'
        VALIDATION_AVENANT = 'VALIDATION_AVENANT', 'Validation d\'Avenant'
    
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

    numero_action = models.CharField(max_length=50, unique=True, null=True, blank=True)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    categorie = models.CharField(max_length=30, choices=CategorieAction.choices, default=CategorieAction.FONCTIONNEMENT)
    centres = models.ManyToManyField(Centre, blank=True, related_name='actions', verbose_name="Centres Concernés")
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
    
    # ==============================================================================
    # NOUVELLE MÉTHODE SAVE POUR APPLIQUER LA RÈGLE MÉTIER
    # ==============================================================================
    def save(self, *args, **kwargs):
        # Si le statut est "Validée", on force l'avancement à 100%.
        if self.statut == self.StatutAction.VALIDEE:
            self.avancement = 100
        super().save(*args, **kwargs) # On appelle ensuite la logique de sauvegarde normale

    class Meta:
        ordering = ['echeance', 'priorite']

    def __str__(self):
        return self.numero_action or self.titre or str(self.id)

# ==============================================================================
# MODÈLES DE SUPPORT
# ==============================================================================
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