# ==============================================================================
# Fichier : core/models/vols.py
# Modèles de données pour la gestion des vols et des clients.
# ==============================================================================

from django.db import models
from .rh import Agent, Centre  # Import relatif depuis le fichier rh.py du même paquet

# ==============================================================================
# SECTION II : GESTION DES VOLS
# ==============================================================================

class Client(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    contact = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom']

    def __str__(self):
        return self.nom

class Vol(models.Model):
    ETAT_CHOICES = [
        ("en_attente", "En attente"), 
        ("planifie", "Planifié"), 
        ("en_cours", "En cours"), 
        ("realise", "Réalisé"), 
        ("annule", "Annulé")
    ]
    TYPE_VOL_CHOICES = [("CAG", "CAG"), ("CAM", "CAM")]
    
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='vols')
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='vols')
    cca = models.ForeignKey(
        Agent, 
        on_delete=models.PROTECT, 
        related_name='vols_en_charge_cca', 
        help_text="Agent en charge de la coordination du vol (CCA)"
    )
    date_demande = models.DateField(auto_now_add=True)
    date_vol = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    etat = models.CharField(max_length=50, choices=ETAT_CHOICES, default="en_attente")
    type_vol = models.CharField(max_length=10, choices=TYPE_VOL_CHOICES)
    commentaire = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Vol"
        verbose_name_plural = "Vols"
        ordering = ['-date_vol', 'heure_debut']

    def __str__(self):
        return f"Vol {self.type_vol} pour {self.client} le {self.date_vol}"

class ControleVol(models.Model):
    vol = models.ForeignKey(Vol, on_delete=models.CASCADE, related_name='prises_en_charge')
    controleur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='vols_controles')
    heure_prise_en_charge = models.DateTimeField()
    heure_fin_prise_en_charge = models.DateTimeField()
    type_vol = models.CharField(
        max_length=10, 
        choices=Vol.TYPE_VOL_CHOICES, 
        help_text="Type de contrôle réellement effectué"
    )
    
    class Meta:
        verbose_name = "Prise en charge de vol"
        verbose_name_plural = "Prises en charge de vols"
        ordering = ['heure_prise_en_charge']

    def __str__(self):
        return f"Contrôle de {self.vol} par {self.controleur}"

class AuditHeuresControle(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='audits_heures')
    periode = models.CharField(max_length=50, help_text="Format libre, ex: '2024-Q1', '2024-03'")
    heures_CAG = models.FloatField(default=0.0)
    heures_CAM = models.FloatField(default=0.0)
    date_audit = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Audit d'heures de contrôle"
        verbose_name_plural = "Audits d'heures de contrôle"
        unique_together = ('agent', 'periode')

    def __str__(self):
        return f"Audit heures de {self.agent} pour la période {self.periode}"