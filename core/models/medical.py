# Fichier : core/models/medical.py

from django.db import models
from .rh import Agent # Import depuis le module voisin

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
    class Meta:
        ordering = ['-date_visite']
        verbose_name = "Certificat Médical"
        verbose_name_plural = "Certificats Médicaux"

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

    class Meta:
        ordering = ['-date_heure_rdv']
        verbose_name = "Rendez-vous Médical"
        verbose_name_plural = "Rendez-vous Médicaux"