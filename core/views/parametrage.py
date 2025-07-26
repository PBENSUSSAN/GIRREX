# ==============================================================================
# Fichier : core/models/parametrage.py
# Modèles de données pour le paramétrage dynamique et la gestion des rôles.
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from .rh import Agent, Centre  # Import relatif depuis le fichier rh.py du même paquet

# ==============================================================================
# SECTION III : PARAMETRAGE DYNAMIQUE ET GESTION DES ROLES
# ==============================================================================

class Parametre(models.Model):
    TYPE_VALEUR_CHOICES = [
        ('string', 'Texte'), 
        ('integer', 'Entier'), 
        ('boolean', 'Booléen'), 
        ('date', 'Date')
    ]
    
    nom = models.CharField(max_length=100, unique=True, help_text="Nom technique du paramètre")
    description = models.TextField()
    valeur_defaut = models.CharField(max_length=255)
    type_valeur = models.CharField(max_length=50, choices=TYPE_VALEUR_CHOICES)
    
    class Meta:
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"

    def __str__(self):
        return self.nom

class ValeurParametre(models.Model):
    parametre = models.ForeignKey(Parametre, on_delete=models.CASCADE, related_name='valeurs')
    valeur = models.CharField(max_length=255)
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        null=True, blank=True, 
        help_text="Si ce paramètre est spécifique à un centre"
    )
    responsable = models.ForeignKey(Agent, on_delete=models.PROTECT, help_text="Agent responsable de cette valeur")
    est_global = models.BooleanField(default=False, help_text="Cochez si la valeur s'applique à tous les centres")
    
    class Meta:
        verbose_name = "Valeur de Paramètre"
        verbose_name_plural = "Valeurs de Paramètres"
        unique_together = ('parametre', 'centre')

    def __str__(self):
        scope = f"pour {self.centre.code_centre}" if self.centre else "global"
        return f"{self.parametre.nom} ({scope}) = {self.valeur}"

class Role(models.Model):
    class RoleScope(models.TextChoices):
        CENTRAL = 'CENTRAL', 'Central'
        LOCAL = 'LOCAL', 'Local'
        OPERATIONNEL = 'OPERATIONNEL', 'Opérationnel'
        
    class RoleLevel(models.TextChoices):
        ENCADREMENT = 'ENCADREMENT', 'Encadrement'
        MANAGEMENT = 'MANAGEMENT', 'Management'
        EXECUTION = 'EXECUTION', 'Exécution'
        
    nom = models.CharField(max_length=100, unique=True)
    groups = models.ManyToManyField(
        Group, 
        blank=True, 
        verbose_name="Groupes de permissions associés", 
        help_text="Les ensembles de permissions techniques que ce rôle confère."
    )
    scope = models.CharField(
        max_length=20, 
        choices=RoleScope.choices, 
        verbose_name="Portée du rôle", 
        default=RoleScope.OPERATIONNEL
    )
    level = models.CharField(
        max_length=20, 
        choices=RoleLevel.choices, 
        verbose_name="Niveau hiérarchique", 
        default=RoleLevel.EXECUTION
    )
    
    class Meta:
        verbose_name = "Rôle / Fonction Métier"
        verbose_name_plural = "Rôles / Fonctions Métier"
        ordering = ['scope', 'level', 'nom']

    def __str__(self):
        return self.nom

class AgentRole(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='roles_assignes')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='agents_assignes')
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        null=True, blank=True, 
        help_text="Obligatoire si le rôle est local ou opérationnel."
    )
    date_debut = models.DateField(default=timezone.now, verbose_name="Date de début")
    date_fin = models.DateField(
        null=True, blank=True, 
        verbose_name="Date de fin", 
        help_text="Laisser vide si l'attribution est à durée indéterminée."
    )
    
    class Meta:
        verbose_name = "Attribution de Rôle"
        verbose_name_plural = "Attributions de Rôles"
        unique_together = ('agent', 'role', 'centre', 'date_debut')

    def __str__(self):
        scope = f" @ {self.centre.code_centre}" if self.centre else " (Global)"
        return f"{self.agent} a le rôle '{self.role}'{scope}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.agent.user and (self.date_fin is None or self.date_fin >= timezone.now().date()):
            for group in self.role.groups.all():
                self.agent.user.groups.add(group)
    
    def delete(self, *args, **kwargs):
        user = self.agent.user
        role_to_remove = self.role
        super().delete(*args, **kwargs)
        if user and role_to_remove:
            active_roles = AgentRole.objects.filter(agent=self.agent, date_fin__isnull=True).exclude(pk=self.pk)
            for group in role_to_remove.groups.all():
                if not active_roles.filter(role__groups=group).exists():
                    user.groups.remove(group)

class Delegation(models.Model):
    """Trace la délégation temporaire des droits d'un agent à un autre."""
    delegant = models.ForeignKey(
        Agent, 
        on_delete=models.CASCADE, 
        related_name='delegations_donnees',
        help_text="L'agent qui donne ses droits."
    )
    delegataire = models.ForeignKey(
        Agent, 
        on_delete=models.CASCADE, 
        related_name='delegations_recues',
        help_text="L'agent qui reçoit les droits (l'intérimaire)."
    )
    date_debut = models.DateField(help_text="Début de la période de délégation.")
    date_fin = models.DateField(help_text="Fin de la période de délégation.")
    motivee_par = models.CharField(max_length=255, blank=True, help_text="Raison de la délégation (ex: Congés, Déplacement).")
    creee_par = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='delegations_creees',
        help_text="Utilisateur qui a enregistré cette délégation."
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Délégation de droits"
        verbose_name_plural = "Délégations de droits"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.delegant} délègue à {self.delegataire} du {self.date_debut} au {self.date_fin}"