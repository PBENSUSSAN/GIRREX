# ==============================================================================
# Fichier : core/models/planning.py
# Modèles de données pour la gestion du Tour de Service (Planning).
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .rh import Agent, Centre  # Import relatif depuis le fichier rh.py du même paquet

# ==============================================================================
# SECTION VII : GESTION DU TOUR DE SERVICE
# ==============================================================================

class PositionJour(models.Model):
    """
    Définit le catalogue des positions/postes assignables dans le planning.
    Chaque centre gère sa propre liste de positions.
    """
    class Categorie(models.TextChoices):
        CONTROLE = 'CONTROLE', 'Contrôle'
        AUTRES = 'AUTRES', 'Autres'
        ABSENT = 'ABSENT', 'Absent'

    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name='positions_jour', 
        verbose_name="Centre associé"
    )
    nom = models.CharField(
        max_length=20, 
        help_text="Nom court et unique de la position (ex: 'J1', 'Q2', 'RTT', 'MIS')"
    )
    description = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Description complète (ex: 'Journée normale', 'Mission extérieure')"
    )
    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        verbose_name="Catégorie",
        help_text="Classification de la position pour les statistiques et règles."
    )
    couleur = models.CharField(
        max_length=7, 
        default='#FFFFFF', 
        help_text="Code couleur hexadécimal (ex: #4169E1). Le blanc est la couleur par défaut."
    )

    class Meta:
        verbose_name = "Position Jour (Planning)"
        verbose_name_plural = "Positions Jour (Planning)"
        unique_together = ('centre', 'nom')
        ordering = ['centre', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.centre.code_centre})"

class TourDeService(models.Model):
    """
    Représente l'affectation d'un agent pour une journée spécifique.
    
    Si agent_id est NULL, c'est un commentaire pour la JOURNÉE entière (pas pour un agent spécifique).
    """
    agent = models.ForeignKey(
        Agent, 
        on_delete=models.CASCADE, 
        related_name='tours_de_service',
        null=True,  # ✅ NOUVEAU : Permet commentaire jour (agent=NULL)
        blank=True
    )
    date = models.DateField(db_index=True)
    position_matin = models.ForeignKey(
        PositionJour, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='affectations_matin'
    )
    position_apres_midi = models.ForeignKey(
        PositionJour, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='affectations_apres_midi'
    )
    commentaire = models.TextField(blank=True, null=True)
    modifie_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    class Meta:
        verbose_name = "Tour de Service"
        verbose_name_plural = "Tours de Service"
        # ✅ MODIFIÉ : unique_together enlevé car on peut avoir :
        # - Une entrée par (agent, date) pour les affectations
        # - Une entrée avec (agent=NULL, date) pour le commentaire jour
        # On ajoute une contrainte unique au niveau DB plus tard si nécessaire
        ordering = ['-date', 'agent']

    def __str__(self):
        return f"Tour de {self.agent} le {self.date}"

class TourDeServiceHistorique(models.Model):
    """Trace complète des modifications apportées à un tour de service."""
    class TypeModification(models.TextChoices):
        CREATION = 'CREATION', 'Création'
        MODIFICATION = 'MODIFICATION', 'Modification'

    tour_de_service_original = models.ForeignKey(TourDeService, on_delete=models.SET_NULL, null=True, related_name='historique')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, related_name='+')
    date = models.DateField()
    position_matin = models.ForeignKey(PositionJour, on_delete=models.SET_NULL, null=True, related_name='+')
    position_apres_midi = models.ForeignKey(PositionJour, on_delete=models.SET_NULL, null=True, related_name='+')
    commentaire = models.TextField(blank=True, null=True)
    modifie_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='historique_tours_modifies')
    modifie_le = models.DateTimeField()
    type_modification = models.CharField(max_length=20, choices=TypeModification.choices)

    class Meta:
        verbose_name = "Historique de Tour de Service"
        verbose_name_plural = "Historiques des Tours de Service"
        ordering = ['-modifie_le']

    def __str__(self):
        return f"Historique pour {self.agent} le {self.date} ({self.modifie_le.strftime('%d/%m/%Y %H:%M')})"

class VersionTourDeService(models.Model):
    """
    Représente un "instantané" validé du planning d'un centre pour un mois donné.
    """
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name='versions_planning'
    )
    annee = models.IntegerField(help_text="L'année du planning (ex: 2025)")
    mois = models.IntegerField(help_text="Le mois du planning (ex: 7 pour Juillet)")
    numero_version = models.CharField(
        max_length=20,
        editable=False,
        help_text="Identifiant unique de la version (ex: 072025-1)"
    )
    valide_par = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        help_text="L'utilisateur qui a validé cette version."
    )
    date_validation = models.DateTimeField(
        auto_now_add=True, 
        help_text="La date et l'heure exactes de la validation."
    )
    donnees_planning = models.JSONField(
        help_text="Snapshot complet du planning au moment de la validation."
    )

    class Meta:
        verbose_name = "Version Validée de Tour de Service"
        verbose_name_plural = "Versions Validées de Tour de Service"
        ordering = ['-annee', '-mois', '-date_validation']

    def __str__(self):
        return f"Version du {self.mois}/{self.annee} pour {self.centre.code_centre} (validée le {self.date_validation.strftime('%d/%m/%Y')})"