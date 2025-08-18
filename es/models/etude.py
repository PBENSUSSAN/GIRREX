

from django.db import models # ### CORRECTION ### : Import principal manquant
from django.conf import settings # ### CORRECTION ### : Import pour les relations utilisateur (non utilisé ici, mais bonne pratique)
from django.core.validators import MinValueValidator, MaxValueValidator # ### CORRECTION ### : Import manquant pour les validateurs
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation # ### CORRECTION ### : Import manquant pour les relations génériques
from django.contrib.contenttypes.models import ContentType # ### CORRECTION ### : Import manquant
from core.models import Agent # ### CORRECTION ### : Il manquait l'import du modèle Agent


from .changement import Changement




# ==============================================================================
# 2. MODÈLE ETUDE DE SÉCURITÉ : LE DOSSIER TECHNIQUE
# ==============================================================================
class EtudeSecurite(models.Model):
    class StatutEtude(models.TextChoices):
        INITIALISATION = 'INITIALISATION', 'Initialisation'
        INSTRUCTION_EN_COURS = 'INSTRUCTION_COURS', 'Instruction en cours'
        VALIDATION_FINALE = 'VALIDATION_FINALE', 'En attente de validation finale'
        CLOTUREE = 'CLOTUREE', 'Clôturée'
    class TypeEtude(models.TextChoices):
        DOSSIER_SECURITE = 'DOSSIER_SECURITE', 'Dossier de Sécurité (Complet)'
        EPIS = 'EPIS', 'Étude Prestataire d’Impact sur la Sécurité (EPIS)'
        DSSL = 'DSSL', 'Démonstration de Sécurité Simplifiée Locale (DSSL)'
    reference_etude = models.CharField(max_length=50, unique=True, verbose_name="Référence de l'étude")
    changement = models.OneToOneField(Changement, on_delete=models.CASCADE, related_name='etude_securite')
    type_etude = models.CharField(max_length=20, choices=TypeEtude.choices, default=TypeEtude.DOSSIER_SECURITE)
    plan_securite_pdf = models.FileField(upload_to='es/plans_securite/%Y/%m/', null=True, blank=True, verbose_name="Plan de Sécurité (Annexe 4)")
    fichier_approbation_finale = models.FileField(upload_to='es/approbations/%Y/%m/', null=True, blank=True, verbose_name="Décision d'Approbation Finale (Annexe 5)")
    statut = models.CharField(max_length=30, choices=StatutEtude.choices, default=StatutEtude.INITIALISATION)
    avancement = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Avancement")
    created_at = models.DateTimeField(auto_now_add=True)
    actions_suivi = GenericRelation('suivi.Action')
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
    class NomEtape(models.TextChoices):
        PHASE_PREPARATOIRE = 'PREPA', 'Phase Préparatoire'
        FHA = 'FHA', 'Analyse des Dangers Fonctionnels (FHA)'
        PSSA = 'PSSA', 'Analyse Préliminaire de Sécurité (PSSA)'
        SSA = 'SSA', 'Analyse de Sécurité du Système (SSA)'
    etude = models.ForeignKey(EtudeSecurite, on_delete=models.CASCADE, related_name='etapes')
    nom = models.CharField(max_length=10, choices=NomEtape.choices)
    document_preuve = models.FileField(upload_to='es/preuves/%Y/%m/', null=True, blank=True, verbose_name="Document de Preuve")
    mrr_identifies = models.TextField(blank=True, verbose_name="MRR identifiés à cette étape", help_text="Un MRR par ligne. Ces MRR généreront des actions de suivi lors de la validation nationale.")
    validee_par_local = models.BooleanField(default=False, verbose_name="Validée par ES Local")
    date_validation_local = models.DateTimeField(null=True, blank=True)
    validee_par_national = models.BooleanField(default=False, verbose_name="Validée par ES National")
    date_validation_national = models.DateTimeField(null=True, blank=True)
    class Meta:
        verbose_name = "Étape d'Étude de Sécurité"
        verbose_name_plural = "Étapes des Études de Sécurité"
        ordering = ['etude', 'id']
        unique_together = ('etude', 'nom')
    def __str__(self):
        return f"{self.etude.reference_etude} - {self.get_nom_display()}"

# ==============================================================================
# 4. MODÈLE COMMENTAIRE : LE JOURNAL D'AUDIT DES ÉCHANGES
# ==============================================================================
class CommentaireEtude(models.Model):
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

# ==============================================================================
# 5. MODÈLE MRR : POUR TRACER LES MOYENS EN RÉDUCTION DE RISQUE
# ==============================================================================
class MRR(models.Model):
    etude = models.ForeignKey(EtudeSecurite, on_delete=models.CASCADE, related_name='mrrs')
    description = models.TextField(verbose_name="Description du MRR")
    auteur = models.ForeignKey(Agent, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Moyen en Réduction de Risque (MRR)"
        verbose_name_plural = "Moyens en Réduction de Risque (MRR)"
        ordering = ['-created_at']
    def __str__(self):
        return f"MRR #{self.id} pour l'étude {self.etude.reference_etude}"