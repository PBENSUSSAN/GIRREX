# Fichier : es/apps.py

from django.apps import AppConfig

class EsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "es"

    def ready(self):
        # Cette méthode est appelée par Django quand l'application est prête.
        # On importe nos signaux ici pour les connecter.
        import es.signals