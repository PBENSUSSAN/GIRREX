# Fichier : girrex_project/settings.py (Version Corrigée)

import os
from pathlib import Path

# BASE_DIR pointe vers le dossier racine du projet (contenant manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Clé secrète pour les fonctions cryptographiques de Django. Ne pas partager en production.
SECRET_KEY = "django-insecure-mz1%ypg%n!qktwkp!8p&mmbvvmuk)j65&nr$7+604y76@)oo6!"

# Mode DEBUG activé pour le développement. À mettre sur False en production.
DEBUG = True

# Hôtes autorisés à se connecter. À remplir pour la production.
ALLOWED_HOSTS = []


# ==============================================================================
# APPLICATIONS INSTALLÉES
# ==============================================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'core',
    'suivi',
    'documentation',
    'technique',
    'qs',
    'es',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',

]


# ==============================================================================
# MIDDLEWARE (ORDRE CORRIGÉ ET NETTOYÉ)
# ==============================================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", # D'abord l'authentification
    "django.contrib.messages.middleware.MessageMiddleware",
    
    # ENSUITE, notre middleware personnalisé qui dépend de request.user
    "core.middleware.GirrexContextMiddleware", 
    
    # Le NoCacheMiddleware (une seule fois)
    "core.middleware.NoCacheMiddleware",  
    
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Point d'entrée pour les URLs du projet.
ROOT_URLCONF = "girrex_project.urls"

# Point d'entrée pour l'application WSGI (utilisé en production).
WSGI_APPLICATION = "girrex_project.wsgi.application"


# ==============================================================================
# BASES DE DONNÉES
# ==============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ==============================================================================
# TEMPLATES (PROCESSEUR DE CONTEXTE NETTOYÉ)
# ==============================================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                'django.template.context_processors.debug',
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                
                # Uniquement le processeur de contexte global. 
                # L'autre est maintenant géré par le middleware.
                'core.context_processors.girrex_global_context',
            ],
        },
    },
]


# ==============================================================================
# AUTRES CONFIGURATIONS (INCHANGÉES)
# ==============================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = None
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')