# Fichier : es/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Changement, EtudeSecurite, EtapeEtude

# Le signal qui créait automatiquement l'étude est maintenant désactivé.
# La logique est déplacée dans la vue `classifier_changement_view` pour un meilleur contrôle.
# Nous gardons ce fichier pour de futures automatisations si nécessaire.