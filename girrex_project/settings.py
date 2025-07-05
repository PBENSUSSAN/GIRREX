# Fichier : girrex_project/settings.py (Version nettoyée)

"""
Django settings for girrex_project project.
... (le reste du docstring est bon) ...
"""
import os
from pathlib import Path

# === CHEMINS DE BASE ===
BASE_DIR = Path(__file__).resolve().parent.parent


# === PARAMÈTRES DE SÉCURITÉ ET DÉVELOPPEMENT ===
# ATTENTION : Ces valeurs doivent être changées pour la production
SECRET_KEY = "django-insecure-mz1%ypg%n!qktwkp!8p&mmbvvmuk)j65&nr$7+604y76@)oo6!"
DEBUG = True
ALLOWED_HOSTS = []


# === CONFIGURATION DE L'APPLICATION ===
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'core',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.NoCacheMiddleware",  
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "girrex_project.urls"
WSGI_APPLICATION = "girrex_project.wsgi.application"


# === BASE DE DONNÉES ===
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# === GESTION DES TEMPLATES ===
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
                'core.context_processors.user_roles_processor',
            ],
        },
    },
]


# === GESTION DES FICHIERS STATIQUES (CSS, IMAGES, JS) ===
# L'URL pour y accéder dans le navigateur
STATIC_URL = 'static/'
# Le dossier où Django collectera tous les fichiers statiques pour la production
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Utile pour le déploiement
# Les dossiers où Django cherche les fichiers statiques de votre projet
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


# === GESTION DE L'AUTHENTIFICATION ===
# --- REDIRECTIONS APRÈS CONNEXION/DÉCONNEXION ---
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# --- VALIDATEURS DE MOT DE PASSE ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# === INTERNATIONALISATION ===
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = "fr-fr" # <--- Suggestion : passez-le en français
TIME_ZONE = "Europe/Paris" # <--- Suggestion : utilisez votre fuseau horaire
USE_I18N = True
USE_TZ = True


# === CLÉ PRIMAIRE PAR DÉFAUT ===
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"