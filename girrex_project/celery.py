# Fichier : girrex_project/celery.py

import os
from celery import Celery

# Définir le module de settings par défaut pour Django. C'est toujours nécessaire.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "girrex_project.settings")

# Créer l'instance de l'application Celery
app = Celery("girrex_project")

# ==============================================================================
# CONFIGURATION DIRECTE ET FORCÉE
# ==============================================================================
# Au lieu de lire le fichier settings.py (ce qui semble échouer),
# nous mettons à jour la configuration de l'application directement ici.
# C'est la méthode la plus robuste pour le débogage.

app.conf.update(
    # On force l'exécution locale et synchrone des tâches
    task_always_eager=True,
    
    # On spécifie un "broker" qui fonctionne en mémoire
    broker_url='memory://',
    
    # On désactive le stockage des résultats
    result_backend=None
)
# ==============================================================================

# On commente cette ligne, car nous venons de faire la configuration manuellement.
# app.config_from_object("django.conf:settings", namespace="CELERY")

# Charger automatiquement les modules de tâches depuis toutes les applications Django enregistrées.
app.autodiscover_tasks()