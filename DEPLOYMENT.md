# 🚀 Guide de Déploiement GIRREX

Ce guide vous accompagne dans le déploiement de GIRREX en production.

## 📋 Prérequis

### Serveur
- Ubuntu 20.04 LTS ou supérieur (recommandé)
- Minimum 2 GB RAM
- 20 GB d'espace disque
- Accès root ou sudo

### Logiciels requis
- Python 3.13+
- PostgreSQL 14+
- Redis 6+
- Nginx
- Supervisor (pour Celery)

---

## 🔧 Installation du Serveur

### 1. Mise à jour du système

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Installation de Python et dépendances

```bash
sudo apt install python3.13 python3.13-venv python3.13-dev python3-pip -y
sudo apt install build-essential libpq-dev -y
```

### 3. Installation de PostgreSQL

```bash
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

Créer la base de données :

```bash
sudo -u postgres psql

-- Dans psql :
CREATE DATABASE girrex_db;
CREATE USER girrex_user WITH PASSWORD 'votre_mot_de_passe_securise';
ALTER ROLE girrex_user SET client_encoding TO 'utf8';
ALTER ROLE girrex_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE girrex_user SET timezone TO 'Europe/Paris';
GRANT ALL PRIVILEGES ON DATABASE girrex_db TO girrex_user;
\q
```

### 4. Installation de Redis

```bash
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis
```

Tester Redis :

```bash
redis-cli ping
# Doit retourner : PONG
```

### 5. Installation de Nginx

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## 📦 Déploiement de l'Application

### 1. Créer un utilisateur dédié

```bash
sudo adduser girrex --disabled-password --gecos ""
sudo su - girrex
```

### 2. Cloner ou transférer le projet

```bash
# Si utilisation de Git :
cd /home/girrex
git clone <repository_url> girrex_app

# Ou transférer via SCP/SFTP
```

### 3. Créer l'environnement virtuel

```bash
cd /home/girrex/girrex_app
python3.13 -m venv venv
source venv/bin/activate
```

### 4. Installer les dépendances

Modifier d'abord `requirements.txt` pour décommenter les packages de production :

```bash
# Décommenter dans requirements.txt :
# - psycopg2-binary
# - gunicorn
# - redis
# - celery[redis]
# - sentry-sdk (optionnel)
```

Puis installer :

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configuration de l'environnement

```bash
cp .env.example .env
nano .env
```

Configurer les variables (voir `.env.example` pour les détails) :

```bash
DJANGO_SECRET_KEY=<générer une nouvelle clé>
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DATABASE_URL=postgresql://girrex_user:mot_de_passe@localhost:5432/girrex_db
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 6. Modifier settings.py pour la production

Créer un fichier `girrex_project/settings_prod.py` :

```python
from .settings import *
import os

# Sécurité
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Base de données
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Celery
CELERY_TASK_ALWAYS_EAGER = False
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Fichiers statiques
STATIC_ROOT = '/var/www/girrex/static/'
MEDIA_ROOT = '/var/www/girrex/media/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/girrex/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### 7. Appliquer les migrations

```bash
export DJANGO_SETTINGS_MODULE=girrex_project.settings_prod
source .env  # Charger les variables d'environnement

python manage.py migrate
```

### 8. Créer le superutilisateur

```bash
python manage.py createsuperuser
```

### 9. Collecter les fichiers statiques

```bash
sudo mkdir -p /var/www/girrex/static
sudo mkdir -p /var/www/girrex/media
sudo chown -R girrex:girrex /var/www/girrex

python manage.py collectstatic --noinput
```

### 10. Créer les dossiers de logs

```bash
sudo mkdir -p /var/log/girrex
sudo chown -R girrex:girrex /var/log/girrex
```

---

## ⚙️ Configuration de Gunicorn

### 1. Créer le fichier de configuration

```bash
nano /home/girrex/girrex_app/gunicorn_config.py
```

Contenu :

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "/var/log/girrex/gunicorn-error.log"
accesslog = "/var/log/girrex/gunicorn-access.log"
loglevel = "info"
```

### 2. Créer le service systemd

```bash
sudo nano /etc/systemd/system/girrex.service
```

Contenu :

```ini
[Unit]
Description=GIRREX Django Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=girrex
Group=girrex
WorkingDirectory=/home/girrex/girrex_app
EnvironmentFile=/home/girrex/girrex_app/.env
Environment="DJANGO_SETTINGS_MODULE=girrex_project.settings_prod"

ExecStart=/home/girrex/girrex_app/venv/bin/gunicorn \
    --config /home/girrex/girrex_app/gunicorn_config.py \
    girrex_project.wsgi:application

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Démarrer le service

```bash
sudo systemctl daemon-reload
sudo systemctl start girrex
sudo systemctl enable girrex
sudo systemctl status girrex
```

---

## 🔄 Configuration de Celery

### 1. Créer le service Celery Worker

```bash
sudo nano /etc/systemd/system/girrex-celery.service
```

Contenu :

```ini
[Unit]
Description=GIRREX Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=girrex
Group=girrex
WorkingDirectory=/home/girrex/girrex_app
EnvironmentFile=/home/girrex/girrex_app/.env
Environment="DJANGO_SETTINGS_MODULE=girrex_project.settings_prod"

ExecStart=/home/girrex/girrex_app/venv/bin/celery -A girrex_project worker \
    --loglevel=info \
    --logfile=/var/log/girrex/celery-worker.log \
    --pidfile=/var/run/celery/worker.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Créer le dossier PID

```bash
sudo mkdir -p /var/run/celery
sudo chown girrex:girrex /var/run/celery
```

### 3. Démarrer Celery

```bash
sudo systemctl daemon-reload
sudo systemctl start girrex-celery
sudo systemctl enable girrex-celery
sudo systemctl status girrex-celery
```

---

## 🌐 Configuration de Nginx

### 1. Créer la configuration du site

```bash
sudo nano /etc/nginx/sites-available/girrex
```

Contenu :

```nginx
upstream girrex_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    # Redirection HTTP vers HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;

    # Certificats SSL (Let's Encrypt recommandé)
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logs
    access_log /var/log/nginx/girrex-access.log;
    error_log /var/log/nginx/girrex-error.log;

    # Upload size
    client_max_body_size 100M;

    # Fichiers statiques
    location /static/ {
        alias /var/www/girrex/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers media
    location /media/ {
        alias /var/www/girrex/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Application Django
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_buffering off;

        proxy_pass http://girrex_app;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

### 2. Activer le site

```bash
sudo ln -s /etc/nginx/sites-available/girrex /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔐 Configuration SSL avec Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

Renouvellement automatique :

```bash
sudo certbot renew --dry-run
```

---

## 📊 Monitoring et Maintenance

### Logs à surveiller

```bash
# Logs Django
tail -f /var/log/girrex/django.log

# Logs Gunicorn
tail -f /var/log/girrex/gunicorn-error.log

# Logs Celery
tail -f /var/log/girrex/celery-worker.log

# Logs Nginx
tail -f /var/log/nginx/girrex-error.log
```

### Commandes utiles

```bash
# Redémarrer l'application
sudo systemctl restart girrex

# Redémarrer Celery
sudo systemctl restart girrex-celery

# Redémarrer Nginx
sudo systemctl restart nginx

# Vérifier les services
sudo systemctl status girrex
sudo systemctl status girrex-celery
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis
```

### Backup de la base de données

```bash
# Créer un backup
sudo -u postgres pg_dump girrex_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurer un backup
sudo -u postgres psql girrex_db < backup_20250101_120000.sql
```

---

## 🔄 Mise à jour de l'Application

```bash
# Se connecter en tant qu'utilisateur girrex
sudo su - girrex

# Aller dans le dossier de l'app
cd /home/girrex/girrex_app

# Activer l'environnement virtuel
source venv/bin/activate

# Récupérer les mises à jour
git pull origin main

# Installer les nouvelles dépendances
pip install -r requirements.txt

# Appliquer les migrations
export DJANGO_SETTINGS_MODULE=girrex_project.settings_prod
source .env
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Redémarrer les services
exit  # Sortir de l'utilisateur girrex
sudo systemctl restart girrex
sudo systemctl restart girrex-celery
```

---

## ✅ Checklist de Déploiement

- [ ] Serveur configuré (Python, PostgreSQL, Redis, Nginx)
- [ ] Base de données créée
- [ ] Application transférée sur le serveur
- [ ] Environnement virtuel créé
- [ ] Dépendances installées
- [ ] Fichier .env configuré
- [ ] Migrations appliquées
- [ ] Superutilisateur créé
- [ ] Fichiers statiques collectés
- [ ] Service Gunicorn configuré et démarré
- [ ] Service Celery configuré et démarré
- [ ] Nginx configuré
- [ ] Certificat SSL installé
- [ ] Logs fonctionnels
- [ ] Backup configuré

---

## 🆘 Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u girrex -n 50

# Vérifier la configuration
sudo systemctl status girrex
```

### Erreur 502 Bad Gateway

```bash
# Vérifier que Gunicorn tourne
sudo systemctl status girrex

# Vérifier les logs Nginx
tail -f /var/log/nginx/girrex-error.log
```

### Problèmes de base de données

```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Se connecter à la DB
sudo -u postgres psql girrex_db
```

### Celery ne traite pas les tâches

```bash
# Vérifier Redis
redis-cli ping

# Vérifier Celery
sudo systemctl status girrex-celery
tail -f /var/log/girrex/celery-worker.log
```

---

**Note** : Adapter ce guide selon votre infrastructure spécifique.

*Dernière mise à jour : Octobre 2025*
