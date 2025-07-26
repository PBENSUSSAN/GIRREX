# Fichier : core/models/service_journalier.py

from django.db import models
from .rh import Agent, Centre
from django.conf import settings

class ServiceJournalier(models.Model):
    """
    Trace l'état d'une journée de service pour un centre.
    Ce modèle remplace FeuilleTempsCloture et ajoute la notion de "Visa"
    par un responsable après clôture.
    """
    class StatutJournee(models.TextChoices):
        OUVERTE = 'OUVERTE', 'Ouverte'
        CLOTUREE = 'CLOTUREE', 'Clôturée'
        VISEE = 'VISEE', 'Visée' # Nouveau statut pour la signature

    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name="services_journaliers")
    date_jour = models.DateField(db_index=True)
    
    # --- Informations d'ouverture ---
    cdq_ouverture = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='services_ouverts', verbose_name="CDQ d'ouverture")
    heure_ouverture = models.TimeField(verbose_name="Heure d'ouverture")
    ouvert_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='journees_initialisees')

    # --- Informations de clôture (optionnelles) ---
    cdq_cloture = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='services_clotures', null=True, blank=True, verbose_name="CDQ de clôture")
    heure_cloture = models.TimeField(null=True, blank=True, verbose_name="Heure de clôture")
    cloture_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='journees_cloturees_trace', null=True, blank=True)
    
    # --- NOUVEAU : Informations de Visa (Signature) ---
    vise_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='services_vises',
        null=True, blank=True,
        verbose_name="Visé par"
    )
    date_visa = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Date du visa"
    )
    # --- FIN DU NOUVEAU BLOC ---

    statut = models.CharField(max_length=10, choices=StatutJournee.choices, default=StatutJournee.OUVERTE)

    class Meta:
        verbose_name = "Service Journalier"
        verbose_name_plural = "Services Journaliers"
        unique_together = ('centre', 'date_jour')
        ordering = ['-date_jour', 'centre']
        permissions = [
            ("open_close_service", "Peut ouvrir et clôturer le service journalier"),
            ("visa_service", "Peut viser un service journalier clôturé"), # Nouvelle permission
        ]

    def __str__(self):
        return f"Service du {self.date_jour} pour {self.centre.code_centre} ({self.statut})"