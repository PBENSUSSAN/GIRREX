# Fichier : es/models.py

from django.db import models
from django.conf import settings
from core.models import Agent, Centre

# ==============================================================================
# 1. MODÈLE CHANGEMENT : LE DOSSIER ADMINISTRATIF
# ==============================================================================
class Changement(models.Model):
    """
    Représente le dossier administratif d'un changement, initiant et encadrant
    le processus d'étude de sécurité.
    """
    class Classification(models.TextChoices):
        NON_DEFINI = 'NON_DEFINI', 'Non Défini'
        SUIVI = 'SUIVI', 'Suivi'
        NON_SUIVI = 'NON_SUIVI', 'Non Suivi'

    class StatutProcessus(models.TextChoices):
        NOTIFICATION = 'NOTIFICATION', 'En attente de classification'
        ETUDE_REQUISE = 'ETUDE_REQUISE', 'Étude de sécurité requise'
        REALISATION = 'REALISATION', 'Réalisation'
        CLOS = 'CLOS', 'Clos'

    # --- Identification ---
    titre = models.CharField(max_length=255, verbose_name="Titre / Objet du changement")
    description = models.TextField(verbose_name="Description sommaire du besoin")
    initiateur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='changements_inities', verbose_name="Initiateur (ES Local)")
    centre_principal = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='changements_pilotes', verbose_name="Centre pilote")

    # --- Documents Administratifs Clés ---
    fichier_notification_initiale = models.FileField(upload_to='es/notifications/%Y/%m/', verbose_name="Fichier de Notification (Annexe 1)")
    fichier_reponse_notification = models.FileField(upload_to='es/reponses/%Y/%m/', null=True, blank=True, verbose_name="Fichier de Réponse (Annexe 2)")

    # --- Pilotage par l'Autorité ---
    classification = models.CharField(max_length=20, choices=Classification.choices, default=Classification.NON_DEFINI)
    correspondant_dircam = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='changements_supervises', verbose_name="Correspondant (ES National)")
    
    # --- Suivi global ---
    statut = models.CharField(max_length=20, choices=StatutProcessus.choices, default=StatutProcessus.NOTIFICATION)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Processus de Changement"
        verbose_name_plural = "Processus de Changements"
        ordering = ['-created_at']

    def __str__(self):
        return self.titre


# ==============================================================================
# 2. MODÈLE ETUDE DE SÉCURITÉ : LE DOSSIER TECHNIQUE
# ==============================================================================
class EtudeSecurite(models.Model):
    """
    Représente le dossier technique d'une étude de sécurité, contenant les étapes
    méthodologiques, les preuves et les décisions.
    """
    class StatutEtude(models.TextChoices):
        INITIALISATION = 'INITIALISATION', 'Initialisation'
        INSTRUCTION_EN_COURS = 'INSTRUCTION_COURS', 'Instruction en cours'
        VALIDATION_FINALE = 'VALIDATION_FINALE', 'En attente de validation finale'
        CLOTUREE = 'CLOTUREE', 'Clôturée'
    
    class TypeEtude(models.TextChoices):
        DOSSIER_SECURITE = 'DOSSIER_SECURITE', 'Dossier de Sécurité (Complet)'
        EPIS = 'EPIS', 'Étude Prestataire d’Impact sur la Sécurité (EPIS)'
        DSSL = 'DSSL', 'Démonstration de Sécurité Simplifiée Locale (DSSL)'

    # --- Identification et Lien ---
    reference_etude = models.CharField(max_length=50, unique=True, verbose_name="Référence de l'étude")
    changement = models.OneToOneField(Changement, on_delete=models.CASCADE, related_name='etude_securite')
    type_etude = models.CharField(max_length=20, choices=TypeEtude.choices, default=TypeEtude.DOSSIER_SECURITE)

    # --- Documents Transverses ---
    plan_securite_pdf = models.FileField(upload_to='es/plans_securite/%Y/%m/', null=True, blank=True, verbose_name="Plan de Sécurité (Annexe 4)")
    fichier_approbation_finale = models.FileField(upload_to='es/approbations/%Y/%m/', null=True, blank=True, verbose_name="Décision d'Approbation Finale (Annexe 5)")

    # --- Suivi ---
    statut = models.CharField(max_length=30, choices=StatutEtude.choices, default=StatutEtude.INITIALISATION)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Étude de Sécurité"
        verbose_name_plural = "Études de Sécurité"
        ordering = ['-created_at']

    def __str__(self):
        return self.reference_etude


# ==============================================================================
# 3. MODÈLE ETAPE D'ÉTUDE : LES JALONS DU WORKFLOW
# ==============================================================================
class EtapeEtude(models.Model):
    """
    Représente un jalon ou une phase méthodologique d'une étude de sécurité.
    """
    class NomEtape(models.TextChoices):
        PHASE_PREPARATOIRE = 'PREPA', 'Phase Préparatoire'
        FHA = 'FHA', 'Analyse des Dangers Fonctionnels (FHA)'
        PSSA = 'PSSA', 'Analyse Préliminaire de Sécurité (PSSA)'
        SSA = 'SSA', 'Analyse de Sécurité du Système (SSA)'

    etude = models.ForeignKey(EtudeSecurite, on_delete=models.CASCADE, related_name='etapes')
    nom = models.CharField(max_length=10, choices=NomEtape.choices)
    
    # --- Preuves et MRR ---
    document_preuve = models.FileField(upload_to='es/preuves/%Y/%m/', null=True, blank=True, verbose_name="Document de Preuve")
    mrr_identifies = models.TextField(blank=True, verbose_name="MRR identifiés à cette étape", help_text="Un MRR par ligne. Ces MRR généreront des actions de suivi lors de la validation nationale.")

    # --- Double Validation ---
    validee_par_local = models.BooleanField(default=False, verbose_name="Validée par ES Local")
    date_validation_local = models.DateTimeField(null=True, blank=True)
    
    validee_par_national = models.BooleanField(default=False, verbose_name="Validée par ES National")
    date_validation_national = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Étape d'Étude de Sécurité"
        verbose_name_plural = "Étapes des Études de Sécurité"
        ordering = ['etude', 'id'] # Ordre de création
        unique_together = ('etude', 'nom') # Une seule étape de chaque nom par étude

    def __str__(self):
        return f"{self.etude.reference_etude} - {self.get_nom_display()}"


# ==============================================================================
# 4. MODÈLE COMMENTAIRE : LE JOURNAL D'AUDIT DES ÉCHANGES
# ==============================================================================
class CommentaireEtude(models.Model):
    """
    Trace un échange ou une décision concernant une étude de sécurité.
    """
    etude = models.ForeignKey(EtudeSecurite, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(Agent, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField()
    piece_jointe = models.FileField(upload_to='es/commentaires_pj/%Y/%m/', null=True, blank=True)

    class Meta:
        verbose_name = "Commentaire d'Étude"
        verbose_name_plural = "Commentaires d'Étude"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Commentaire de {self.auteur} sur {self.etude.reference_etude}"