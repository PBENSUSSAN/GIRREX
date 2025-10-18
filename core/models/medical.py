# Fichier : core/models/medical.py

from django.db import models
from django.contrib.auth import get_user_model
from .rh import Agent

User = get_user_model()

class CertificatMed(models.Model):
    class ClasseAptitude(models.TextChoices):
        CLASSE_3 = 'CLASSE_3', 'Classe 3'

    class ResultatVisite(models.TextChoices):
        APTE = 'APTE', 'Apte'
        INAPTE_TEMPORAIRE = 'INAPTE_TEMP', 'Inapte Temporaire'
        INAPTE_DEFINITIF = 'INAPTE_DEF', 'Inapte Définitif'

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='certificats_medicaux')
    date_visite = models.DateField(verbose_name="Date de la visite")
    organisme_medical = models.CharField(max_length=255, verbose_name="Centre médical")
    resultat = models.CharField(max_length=20, choices=ResultatVisite.choices)
    classe_aptitude = models.CharField(max_length=20, choices=ClasseAptitude.choices, default=ClasseAptitude.CLASSE_3)
    date_expiration_aptitude = models.DateField(verbose_name="Date d'expiration de l'aptitude", null=True, blank=True)
    restrictions = models.TextField(blank=True, help_text="Ex: Port de verres correcteurs obligatoire.")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")
    piece_jointe = models.FileField(
        upload_to='certificats_medicaux/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Scan du certificat (optionnel)"
    )
    
    # Traçabilité
    saisi_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificats_saisis',
        verbose_name="Saisi par"
    )
    date_saisie = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Date de saisie")
    
    class Meta:
        ordering = ['-date_visite']
        verbose_name = "Certificat Médical"
        verbose_name_plural = "Certificats Médicaux"
    
    def __str__(self):
        return f"{self.agent.trigram} - {self.get_resultat_display()} ({self.date_visite.strftime('%d/%m/%Y')})"
    
    @property
    def est_valide_aujourdhui(self):
        """Vérifie si le certificat est valide aujourd'hui."""
        from datetime import date
        if self.resultat != 'APTE':
            return False
        if not self.date_expiration_aptitude:
            return False
        return self.date_expiration_aptitude >= date.today()
    
    @property
    def jours_avant_expiration(self):
        """Retourne le nombre de jours avant expiration (négatif si expiré)."""
        from datetime import date
        if not self.date_expiration_aptitude:
            return None
        return (self.date_expiration_aptitude - date.today()).days


class RendezVousMedical(models.Model):
    class StatutRDV(models.TextChoices):
        PLANIFIE = 'PLANIFIE', 'Planifié'
        REALISE = 'REALISE', 'Réalisé'
        ANNULE = 'ANNULE', 'Annulé'
        REPORTE = 'REPORTE', 'Reporté'

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='rendez_vous_medicaux')
    date_heure_rdv = models.DateTimeField(verbose_name="Date et heure du rendez-vous")
    organisme_medical = models.CharField(max_length=255, verbose_name="Centre médical")
    type_visite = models.CharField(max_length=100, default="Visite périodique Classe 3")
    statut = models.CharField(max_length=20, choices=StatutRDV.choices, default=StatutRDV.PLANIFIE)
    certificat_genere = models.OneToOneField(CertificatMed, on_delete=models.SET_NULL, null=True, blank=True)
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")
    
    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rdv_crees',
        verbose_name="Créé par"
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rdv_modifies',
        verbose_name="Modifié par"
    )
    date_creation = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Date de modification")

    class Meta:
        ordering = ['-date_heure_rdv']
        verbose_name = "Rendez-vous Médical"
        verbose_name_plural = "Rendez-vous Médicaux"
    
    def __str__(self):
        return f"RDV {self.agent.trigram} - {self.date_heure_rdv.strftime('%d/%m/%Y %Hh%M')} ({self.get_statut_display()})"


# ============================================================================
# NOUVEAUX MODÈLES - Module Suivi Médical Enrichi
# ============================================================================

class CentreMedical(models.Model):
    """
    Liste des centres médicaux agréés pour les visites classe 3.
    Géré via l'admin Django.
    """
    class TypeCentre(models.TextChoices):
        CMPA = 'CMPA', 'Centre Médical des Personnels Aériens'
        HIA = 'HIA', 'Hôpital d\'Instruction des Armées'
        CIVIL = 'CIVIL', 'Centre médical civil agréé'
    
    nom = models.CharField(
        max_length=200, 
        unique=True,
        verbose_name="Nom du centre",
        help_text="Ex: CMPA Aix-en-Provence"
    )
    
    type_centre = models.CharField(
        max_length=20,
        choices=TypeCentre.choices,
        default=TypeCentre.CMPA
    )
    
    adresse = models.TextField(
        blank=True,
        verbose_name="Adresse complète"
    )
    
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone"
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name="Email de contact"
    )
    
    contact_referent = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Contact référent",
        help_text="Ex: Dr DUPONT - Service médecine aéronautique"
    )
    
    delai_moyen_rdv_jours = models.PositiveIntegerField(
        default=30,
        verbose_name="Délai moyen RDV (jours)",
        help_text="Délai habituel pour obtenir un rendez-vous"
    )
    
    actif = models.BooleanField(
        default=True,
        verbose_name="Centre actif",
        help_text="Décocher pour désactiver sans supprimer"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Informations pratiques, horaires, etc."
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nom']
        verbose_name = "Centre Médical"
        verbose_name_plural = "Centres Médicaux"
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_centre_display()})"


class ArretMaladie(models.Model):
    """
    Suivi des arrêts maladie des agents.
    Important pour la gestion de l'aptitude (seuil 21 jours).
    """
    class StatutArret(models.TextChoices):
        EN_COURS = 'EN_COURS', 'En cours'
        CLOTURE = 'CLOTURE', 'Clôturé (reprise effectuée)'
        ANNULE = 'ANNULE', 'Annulé'
    
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='arrets_maladie',
        verbose_name="Agent concerné"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutArret.choices,
        default=StatutArret.EN_COURS,
        verbose_name="Statut de l'arrêt"
    )
    
    date_debut = models.DateField(
        verbose_name="Date de début"
    )
    
    date_fin_prevue = models.DateField(
        verbose_name="Date de fin prévue"
    )
    
    date_fin_reelle = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin réelle",
        help_text="Remplir lors du retour effectif de l'agent"
    )
    
    motif = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Motif (optionnel)",
        help_text="Ex: Grippe, Post-opératoire, etc."
    )
    
    certificat_arret = models.FileField(
        upload_to='arrets_maladie/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Certificat médical (optionnel)"
    )
    
    visite_reprise_requise = models.BooleanField(
        default=False,
        verbose_name="Visite de reprise requise",
        help_text="Automatique si > 21 jours"
    )
    
    visite_reprise_effectuee = models.BooleanField(
        default=False,
        verbose_name="Visite de reprise effectuée"
    )
    
    rdv_reprise = models.ForeignKey(
        RendezVousMedical,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arrets_lies',
        verbose_name="RDV de reprise lié"
    )
    
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    # Champs de clôture
    date_cloture = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de clôture",
        help_text="Date de déclaration de reprise ou d'annulation"
    )
    
    cloture_par = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arrets_clotures',
        verbose_name="Clôturé par"
    )
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de saisie"
    )
    
    class Meta:
        ordering = ['-date_debut']
        verbose_name = "Arrêt Maladie"
        verbose_name_plural = "Arrêts Maladie"
    
    def __str__(self):
        statut_display = f" ({self.get_statut_display()})" if hasattr(self, 'statut') else ""
        return f"{self.agent.trigram} - {self.date_debut.strftime('%d/%m/%Y')} → {self.date_fin_prevue.strftime('%d/%m/%Y')}{statut_display}"
    
    @property
    def duree_jours(self):
        """Calcule la durée en jours (prévue ou réelle)."""
        date_fin = self.date_fin_reelle or self.date_fin_prevue
        return (date_fin - self.date_debut).days + 1  # +1 car inclusif
    
    @property
    def est_long_terme(self):
        """Arrêt > 21 jours = visite de reprise obligatoire."""
        return self.duree_jours > 21
    
    @property
    def jours_ecoules_depuis_debut(self):
        """
        Jours écoulés depuis le début (si EN_COURS).
        Si CLOTURE ou ANNULE, retourne 0.
        """
        from datetime import date
        # Vérifier si le champ statut existe (après migration)
        if not hasattr(self, 'statut') or self.statut != 'EN_COURS':
            return 0
        return (date.today() - self.date_debut).days
    
    @property
    def necessite_pfu(self):
        """
        Vrai si arrêt EN_COURS depuis 90 jours ou plus.
        Déclenche la procédure de suspension MUA.
        """
        return hasattr(self, 'statut') and self.statut == 'EN_COURS' and self.jours_ecoules_depuis_debut >= 90
    
    @property
    def proche_seuil_pfu(self):
        """
        Vrai si arrêt EN_COURS depuis 85 jours ou plus.
        Alerte préventive pour préparer le PFU.
        """
        return hasattr(self, 'statut') and self.statut == 'EN_COURS' and self.jours_ecoules_depuis_debut >= 85
    
    def save(self, *args, **kwargs):
        """
        Override save pour calculer automatiquement si visite reprise requise.
        """
        # Déterminer automatiquement si visite de reprise nécessaire
        if self.duree_jours > 21:
            self.visite_reprise_requise = True
        
        super().save(*args, **kwargs)


class HistoriqueRDV(models.Model):
    """
    Historique complet des actions sur les RDV médicaux.
    Auditabilité totale.
    """
    class TypeAction(models.TextChoices):
        CREATION = 'CREATION', 'Création'
        MODIFICATION = 'MODIFICATION', 'Modification'
        ANNULATION = 'ANNULATION', 'Annulation'
        REALISATION = 'REALISATION', 'Réalisation'
    
    rdv = models.ForeignKey(
        RendezVousMedical,
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name="Rendez-vous concerné"
    )
    
    action = models.CharField(
        max_length=20,
        choices=TypeAction.choices,
        verbose_name="Type d'action"
    )
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions_rdv',
        verbose_name="Utilisateur"
    )
    
    date_action = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de l'action"
    )
    
    # Pour les modifications
    ancien_statut = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Ancien statut"
    )
    
    nouveau_statut = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Nouveau statut"
    )
    
    ancienne_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ancienne date RDV"
    )
    
    nouvelle_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Nouvelle date RDV"
    )
    
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    class Meta:
        ordering = ['-date_action']
        verbose_name = "Historique RDV"
        verbose_name_plural = "Historiques RDV"
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.rdv.agent.trigram} - {self.date_action.strftime('%d/%m/%Y %Hh%M')}"
    
    @property
    def description_complete(self):
        """Génère une description lisible de l'action."""
        user_name = self.utilisateur.agent_profile.trigram if self.utilisateur and hasattr(self.utilisateur, 'agent_profile') else "Système"
        
        if self.action == 'CREATION':
            return f"{user_name} a créé le RDV pour le {self.nouvelle_date.strftime('%d/%m/%Y à %Hh%M') if self.nouvelle_date else '?'}"
        
        elif self.action == 'MODIFICATION':
            if self.ancienne_date and self.nouvelle_date:
                return f"{user_name} a reporté le RDV du {self.ancienne_date.strftime('%d/%m/%Y')} au {self.nouvelle_date.strftime('%d/%m/%Y')}"
            return f"{user_name} a modifié le RDV"
        
        elif self.action == 'ANNULATION':
            return f"{user_name} a annulé le RDV"
        
        elif self.action == 'REALISATION':
            return f"{user_name} a enregistré le résultat de la visite"
        
        return f"{user_name} - {self.get_action_display()}"
