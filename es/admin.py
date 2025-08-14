# Fichier : es/admin.py

from django.contrib import admin
# On importe les modèles que nous avons créés dans es/models.py
from .models import Changement, EtudeSecurite, EtapeEtude, CommentaireEtude

# On enregistre chaque modèle pour qu'il soit visible et gérable dans l'admin.
# Pour l'instant, un enregistrement simple est suffisant.
# Nous pourrons le personnaliser plus tard si nécessaire.

admin.site.register(Changement)
admin.site.register(EtudeSecurite)
admin.site.register(EtapeEtude)
admin.site.register(CommentaireEtude)