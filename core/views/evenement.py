# Fichier : core/models/evenement.py

from django.db import models
from .rh import Agent, Centre

class CategorieEvenement(models.Model):
    """
    Catalogue personnalisable des catégories d'événements pour le Cahier de Marche.
    """
    nom = models.CharField(
        max_length=100,
        help_text="Nom de la catégorie (ex: Météo, Visite, Consigne importante)"
    )
    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name='categories_evenements',
        help_text="Centre auquel cette catégorie est rattachée."
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description courte de ce que couvre cette catégorie."
    )
    couleur = models.CharField(
        max_length=7,
        default='#343a40', # Gris foncé par défaut
        help_text="Code couleur hexadécimal pour l'affichage."
    )

    class Meta:
        verbose_name = "Catégorie d'Événement"
        verbose_name_plural = "Catégories d'Événements"
        unique_together = ('nom', 'centre')
        ordering = ['centre', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.centre.code_centre})"


class EvenementCentre(models.Model):
    """
    Consigne un événement notable non lié à une panne.
    """
    date_heure_evenement = models.DateTimeField(
        db_index=True,
        help_text="Date et heure de l'événement."
    )
    titre = models.CharField(
        max_length=255,
        help_text="Titre court et descriptif de l'événement."
    )
    categorie = models.ForeignKey(
        CategorieEvenement,
        on_delete=models.PROTECT,
        verbose_name="Catégorie",
        related_name='evenements'
    )
    description = models.TextField(
        help_text="Description détaillée de l'événement ou de la consigne."
    )
    centre = models.ForeignKey(
        Centre,
        on_delete=models.PROTECT,
        related_name='evenements'
    )
    auteur = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        related_name='evenements_consignes'
    )
    notification_generale = models.BooleanField(
        default=False,
        verbose_name="Signaler pour notification générale",
        help_text="Cochez cette case si cet événement doit faire l'objet d'une notification."
    )
    cree_le = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Événement Centre"
        verbose_name_plural = "Événements Centre"
        ordering = ['-date_heure_evenement']

    def __str__(self):
        return f"Événement '{self.titre}' sur {self.centre.code_centre} le {self.date_heure_evenement.strftime('%d/%m/%Y')}"