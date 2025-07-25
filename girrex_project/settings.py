# Fichier : girrex_project/settings.py
# Description : Fichier de configuration principal du projet Django GIRREX.
# Cette version inclut la configuration nécessaire pour la librairie django-crispy-forms.

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
# Déclare toutes les applications Django que le projet utilise.
# L'ordre peut être important pour les surcharges de templates ou de statiques.

INSTALLED_APPS = [
    # Applications Django natives
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Notre application principale
    'core',
    
    # APPLICATIONS TIERCES AJOUTÉES
    # 'crispy_forms' gère le rendu avancé des formulaires.
    'crispy_forms',
    # 'crispy_bootstrap5' est le pack de templates pour que crispy-forms génère du HTML compatible Bootstrap 5.
    'crispy_bootstrap5',
]


# ==============================================================================
# MIDDLEWARE
# ==============================================================================
# Les middlewares sont des couches de traitement des requêtes/réponses.
# L'ordre est crucial.

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.NoCacheMiddleware",  # Middleware personnalisé pour désactiver le cache
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
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
# TEMPLATES
# ==============================================================================
# Configuration du moteur de templates de Django.

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')], # Dossier pour les templates globaux (comme base.html)
        "APP_DIRS": True, # Django cherchera aussi les templates dans un dossier "templates" de chaque app.
        "OPTIONS": {
            "context_processors": [
                'django.template.context_processors.debug',
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                
                # Nos context processors personnalisés
                'core.context_processors.effective_permissions_processor',
                'core.context_processors.girrex_global_context',
            ],
        },
    },
]


# ==============================================================================
# FICHIERS STATIQUES (CSS, JAVASCRIPT, IMAGES)
# ==============================================================================

STATIC_URL = 'static/' # URL pour servir les fichiers statiques.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), # Dossier pour les fichiers statiques globaux.
]


# ==============================================================================
# AUTHENTIFICATION
# ==============================================================================

LOGIN_REDIRECT_URL = 'home' # Page vers laquelle rediriger après une connexion réussie.
LOGOUT_REDIRECT_URL = 'login' # Page vers laquelle rediriger après une déconnexion.

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ==============================================================================
# INTERNATIONALISATION
# ==============================================================================

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True


# ==============================================================================
# CONFIGURATION DES CLÉS PRIMAIRES PAR DÉFAUT
# ==============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==============================================================================
# CONFIGURATION POUR DJANGO-CRISPY-FORMS
# ==============================================================================

# Indique les packs de templates que Crispy est autorisé à utiliser.
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# Définit le pack de templates à utiliser par défaut dans tout le projet.
# C'est cette ligne qui corrige l'erreur AttributeError.
CRISPY_TEMPLATE_PACK = "bootstrap5"