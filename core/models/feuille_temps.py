# ==============================================================================
# Fichier : core/models/feuille_temps.py
# Modèles de données pour la gestion des Feuilles de Temps journalières.
# ==============================================================================

from django.db import models
from django.conf import settings # NOUVEAU : Import de settings
from .rh import Agent, Centre

# ==============================================================================
# SECTION VIII : GESTION DES FEUILLES DE TEMPS JOURNALIÈRES
# ==============================================================================

class FeuilleTempsEntree(models.Model):
    """ Stocke une entrée de pointage pour un agent pour un jour donné. """
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='pointages')
    date_jour = models.DateField(db_index=True)
    heure_arrivee = models.TimeField(null=True, blank=True)
    heure_depart = models.TimeField(null=True, blank=True)
    
    # On garde le lien vers User ici, c'est déjà cohérent.
    modifie_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Entrée de Feuille de Temps"
        verbose_name_plural = "Entrées de Feuille de Temps"
        unique_together = ('agent', 'date_jour')
        ordering = ['-date_jour', 'agent']
        
        permissions = [
            ("view_feuilletemps", "Peut voir la feuille de temps journalière"),
            ("change_feuilletemps", "Peut modifier la feuille de temps journalière"),
        ]

    def __str__(self):
        return f"Pointage de {self.agent} le {self.date_jour}"


class FeuilleTempsVerrou(models.Model):
    """ Gère le verrou d'édition pour un centre afin d'éviter les conflits. """
    centre = models.OneToOneField(Centre, on_delete=models.CASCADE, primary_key=True, related_name='verrou_feuille_temps')
    chef_de_quart = models.ForeignKey(Agent, on_delete=models.CASCADE) # <-- On remet le nom original
    verrouille_a = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Verrou d'édition de Feuille de Temps"

    def __str__(self):
        return f"Feuille de temps de {self.centre.code_centre} verrouillée par {self.chef_de_quart}"


# ==============================================================================
# MODÈLE OBSOLÈTE : Ce modèle est maintenant remplacé par ServiceJournalier
# et ServiceJournalierHistorique. Il peut être supprimé ou conservé pour
# archive le temps de la migration des données.
# ==============================================================================
# class FeuilleTempsCloture(models.Model):
#     """ Enregistre la clôture d'une journée de pointage pour un centre. """
#     centre = models.ForeignKey(Centre, on_delete=models.PROTECT)
#     date_jour = models.DateField()
    
#     cloture_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='journees_cloturees')
#     cloture_le = models.DateTimeField(auto_now_add=True)
    
#     reouverte_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='journees_reouvertes')
#     reouverte_le = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         verbose_name = "Journée de Pointage Clôturée (Obsolète)"
#         unique_together = ('centre', 'date_jour')
#         permissions = [
#             ("reouvrir_feuilletemps", "Peut rouvrir une journée de pointage clôturée"),
#         ]

#     def __str__(self):
#         return f"Clôture du {self.date_jour} pour {self.centre.code_centre}"