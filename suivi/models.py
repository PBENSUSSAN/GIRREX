# Fichier : suivi/models.py

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# On importe le modèle Agent depuis l'application 'core'
from core.models import Agent

class ActionQuerySet(models.QuerySet):
    """
    QuerySet personnalisé pour le modèle Action.
    Contient la logique de filtrage réutilisable.
    """
    def for_user(self, user):
        """
        Filtre les actions pour ne renvoyer que celles pertinentes
        pour un utilisateur donné, en fonction de ses droits et de son rôle.
        """
        # Si l'utilisateur est un superutilisateur, il voit tout.
        # Plus tard, on ajoutera ici les rôles "SMS National", etc.
        if user.is_superuser:
            return self.all()
        
        # Si l'utilisateur n'est pas lié à un profil Agent, il ne voit rien.
        if not hasattr(user, 'agent_profile'):
            return self.none() # Renvoie un queryset vide
        
        # Par défaut, un utilisateur standard ne voit que les actions
        # dont il est le responsable OU le validateur.
        agent = user.agent_profile
        return self.filter(
            models.Q(responsable=agent) | models.Q(validateur=agent)
        ).distinct()


class ActionManager(models.Manager):
    """ Manager personnalisé pour le modèle Action. """
    def get_queryset(self):
        return ActionQuerySet(self.model, using=self._db)

    def for_user(self, user):
        """ Raccourci pour appeler la méthode du QuerySet. """
        return self.get_queryset().for_user(user)

class Action(models.Model):
    """
    Modèle central représentant une tâche de suivi. 
    C'est le cœur du "Tableau d'Actions Unique".
    """
    class StatutAction(models.TextChoices):
        A_FAIRE = 'A_FAIRE', 'À faire'
        EN_COURS = 'EN_COURS', 'En cours'
        A_VALIDER = 'A_VALIDER', 'À valider'
        REFUSEE = 'REFUSEE', 'Refusée'
        VALIDEE = 'VALIDEE', 'Validée / Clôturée'
        ARCHIVEE = 'ARCHIVEE', 'Archivée'

    class StatutEcheance(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        DEMANDE_EN_COURS = 'DEMANDE_EN_COURS', 'Demande de réajustement en cours'
    
    class Priorite(models.TextChoices):
        BASSE = 'BASSE', 'Basse'
        MOYENNE = 'MOYENNE', 'Moyenne'
        HAUTE = 'HAUTE', 'Haute'

    # --- Identification et Description ---
    numero_action = models.CharField(max_length=50, unique=True, blank=True, help_text="Ex: ACT-2025-001. Peut être généré automatiquement.")
    titre = models.CharField(max_length=255, verbose_name="Titre / Libellé de l'action")
    description = models.TextField(blank=True, verbose_name="Description détaillée / Livrables attendus")
    
    # --- Responsabilité ---
    responsable = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='actions_a_realiser', verbose_name="Responsable de la réalisation")
    validateur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='actions_a_valider', null=True, blank=True, verbose_name="Validateur de la clôture")
    
    # --- Pilotage et Suivi ---
    statut = models.CharField(max_length=20, choices=StatutAction.choices, default=StatutAction.A_FAIRE)
    priorite = models.CharField(max_length=20, choices=Priorite.choices, default=Priorite.MOYENNE)
    avancement = models.IntegerField(default=0, help_text="Pourcentage de réalisation (0-100)")
    
    # --- Dates et Échéances ---
    date_creation = models.DateTimeField(auto_now_add=True)
    echeance = models.DateField(verbose_name="Échéance initiale")
    date_cloture = models.DateTimeField(null=True, blank=True, verbose_name="Date de clôture effective")
    
    # --- Workflow de Réajustement d'Échéance ---
    statut_echeance = models.CharField(max_length=20, choices=StatutEcheance.choices, default=StatutEcheance.NORMAL)
    echeance_proposee = models.DateField(null=True, blank=True, verbose_name="Nouvelle échéance proposée")
    
    # --- Origine de l'Action (Lien Générique) ---
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, help_text="Le type de modèle à l'origine de l'action (ex: Document, EvenementQS)")
    object_id = models.PositiveIntegerField(help_text="L'ID de l'objet à l'origine de l'action")
    objet_source = GenericForeignKey('content_type', 'object_id')

    # --- Hiérarchie Maître/Esclave ---
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sous_taches', verbose_name="Tâche parente (Maître)")

     # ==============================================================================
    # MODIFICATION 2 : ON ATTACHE LE NOUVEAU MANAGER AU MODÈLE
    # =============================================================================
    objects = ActionManager() 

    def save(self, *args, **kwargs):
        # On exécute cette logique uniquement à la création de l'objet (quand il n'a pas encore de clé primaire)
        if not self.pk:
            # On s'assure que le champ numero_action n'est pas déjà rempli manuellement
            if not self.numero_action:
                current_year = timezone.now().year
                # On cherche la dernière action de l'année courante pour trouver le dernier numéro
                last_action = Action.objects.filter(numero_action__startswith=f'ACT-{current_year}-').order_by('numero_action').last()
                
                new_sequence_number = 1
                if last_action:
                    # On extrait le numéro de séquence (ex: '0001' de 'ACT-2025-0001')
                    last_sequence = int(last_action.numero_action.split('-')[-1])
                    new_sequence_number = last_sequence + 1
                
                # On formate le nouveau numéro avec 4 chiffres, complété par des zéros à gauche
                self.numero_action = f'ACT-{current_year}-{new_sequence_number:04d}'
        
        # On appelle la méthode save() originale de Django pour sauvegarder l'objet
        super().save(*args, **kwargs)
    
    
    class Meta:
        verbose_name = "Action de Suivi"
        verbose_name_plural = "Actions de Suivi"
        ordering = ['echeance', 'priorite']

    def __str__(self):
        return f"{self.numero_action or self.id} - {self.titre}"


class HistoriqueAction(models.Model):
    """
    Modèle d'audit qui trace chaque événement significatif dans la vie d'une Action.
    """
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