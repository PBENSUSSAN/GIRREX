=============================================================================
   _____  _____  _____  _____  ________   __
  / ____|_   _||  __ \|  __ \|  ____\ \ / /
 | |  __  | |  | |__) | |__) | |__   \ V / 
 | | |_ | | |  |  _  /|  _  /|  __|   > <  
 | |__| |_| |_ | | \ \| | \ \| |____ / . \ 
  \_____|_____||_|  \_\_|  \_\______/_/ \_\

  Gestion Intégrée des Ressources et Risques en Essais eXpérimentaux
=============================================================================

VERSION : 0.9 (Développement)
DATE    : Octobre 2025
AUTEUR  : Pascal - DGA Essais en Vol

=============================================================================
                            DESCRIPTION
=============================================================================

GIRREX est une application web Django complète pour la gestion des 
opérations quotidiennes des centres de contrôle aérien DGA Essais en Vol.

Elle couvre l'ensemble du cycle de vie opérationnel :
- Gestion des ressources humaines (agents, licences, qualifications)
- Planification opérationnelle (tours de service, affectations)
- Suivi qualité et sécurité (actions correctives, audits)
- Documentation (gestion documentaire avec versioning)
- Technique (pannes, MISO)
- Cybersécurité (gestion des risques et incidents SMSI)
- Compétences (maintien des compétences, formations)
- Feedback (collecte et traitement des retours)

=============================================================================
                         PRÉREQUIS SYSTÈME
=============================================================================

- Python 3.13 ou supérieur
- Django 5.2
- SQLite (développement) ou PostgreSQL (production)
- 2 GB RAM minimum
- 1 GB espace disque

=============================================================================
                    INSTALLATION RAPIDE (DEV)
=============================================================================

1. CRÉER L'ENVIRONNEMENT VIRTUEL
   
   python -m venv venv
   

2. ACTIVER L'ENVIRONNEMENT VIRTUEL
   
   Windows :
   venv\Scripts\activate
   
   Linux/Mac :
   source venv/bin/activate


3. INSTALLER LES DÉPENDANCES
   
   pip install -r requirements.txt


4. APPLIQUER LES MIGRATIONS
   
   python manage.py migrate


5. CRÉER UN SUPERUTILISATEUR
   
   python manage.py createsuperuser


6. PEUPLER LA BASE (OPTIONNEL)
   
   python manage.py populate_db


7. LANCER LE SERVEUR
   
   python manage.py runserver


8. OUVRIR DANS LE NAVIGATEUR
   
   http://127.0.0.1:8000/
   Admin : http://127.0.0.1:8000/admin/

=============================================================================
                       STRUCTURE DU PROJET
=============================================================================

GIRREX/
├── girrex_project/         Configuration Django principale
├── core/                   Application centrale (RH, planning, médical)
├── suivi/                  Gestion des actions et workflow
├── documentation/          Gestion documentaire
├── technique/              Pannes et MISO
├── qs/                     Qualité & Sécurité
├── es/                     Études de sécurité
├── cyber/                  Cybersécurité (SMSI)
├── feedback/               Retours utilisateurs
├── competences/            Gestion des compétences (MUA)
├── activites/              Suivi des activités opérationnelles
├── templates/              Templates HTML
├── static/                 Fichiers statiques (CSS, JS, images)
├── media/                  Fichiers uploadés (certificats, documents)
├── db.sqlite3              Base de données (dev)
├── manage.py               Outil de gestion Django
├── requirements.txt        Dépendances Python
└── README.md               Documentation complète (Markdown)

=============================================================================
                      COMMANDES UTILES
=============================================================================

# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Lancer le serveur de développement
python manage.py runserver

# Créer un superutilisateur
python manage.py createsuperuser

# Accéder au shell Django
python manage.py shell

# Collecter les fichiers statiques (production)
python manage.py collectstatic

# Lancer les tests
python manage.py test

# Vérifier le code
python check_code.py

# Peupler la base avec des données de test
python manage.py populate_db

=============================================================================
                    MODULES PRINCIPAUX
=============================================================================

CORE
----
- Gestion des agents, centres, licences, qualifications
- Planning opérationnel et tours de service
- Certificats médicaux et rendez-vous
- Gestion des zones et activités
- Système de rôles et délégations avancé

SUIVI
-----
- Actions correctives avec workflow complet
- Sous-tâches hiérarchiques
- Historique et traçabilité
- Réajustement d'échéances avec validation

DOCUMENTATION
-------------
- Gestion documentaire centralisée
- Cycle de vie : En rédaction → En vigueur → Remplacé → Archivé
- Versioning et avenants
- Relecture périodique avec alertes
- Prise en compte par signature numérique

TECHNIQUE
---------
- Gestion des pannes d'équipements
- MISO (Mise en Service Opérationnel)
- Cahier de marche électronique

QS (QUALITÉ & SÉCURITÉ)
-----------------------
- FNE (Fiches de Non-conformité Événementielle)
- Tableau de bord qualité
- Suivi des recommandations

CYBER
-----
- Gestion des risques cyber (EBIOS RM)
- Incidents de sécurité avec remédiation
- Dashboard national SMSI
- Vue locale pour relais SMSI

COMPÉTENCES
-----------
- Dossiers de compétence par agent
- MUA (Maintien d'Usage des Aptitudes)
- Gestion FORM (Formation locale)
- Relevés mensuels

ES (ÉTUDES DE SÉCURITÉ)
-----------------------
- Études de sécurité liées aux changements
- Gestion des changements avec workflow

FEEDBACK
--------
- Collecte des retours utilisateurs
- Catégorisation et traitement
- Statistiques et analyse

ACTIVITÉS
---------
- Saisie des activités journalières
- Supervision CCA
- Timeline des missions

=============================================================================
                      SYSTÈME DE PERMISSIONS
=============================================================================

GIRREX implémente un système de rôles avancé :

RÔLES DISPONIBLES :
- Chef de Division (supervision tous centres)
- Adjoint Chef de Division
- Chef de Centre (gestion d'un centre)
- Adjoint Chef de Centre
- Contrôleur (opérationnel)
- Chef de Quart (validation journalière)
- Coordonateur
- SMS Local (sécurité)
- Responsable SMS (national)
- QS Local (qualité)
- ES Local (études)
- SMSI Local (cybersécurité)
- Adjoint SMSI (cybersécurité national)
- FORM Local (formation)

FONCTIONNALITÉS :
- Un agent peut avoir plusieurs rôles
- Délégations temporaires entre agents
- Context switching (changement de rôle actif)
- Permissions cumulatives
- Filtrage automatique des données selon le contexte

=============================================================================
                         CENTRES GÉRÉS
=============================================================================

- IS : DGA Essais en Vol Istres
- CA : DGA Essais en Vol Cazaux  
- TO : DGA Essais en Vol Toulouse
- BN : DGA Essais en Vol Brétigny
- CC : Coordination Centre Aéromobile (CCA)

Chaque centre peut avoir :
- Ses propres agents
- Son planning indépendant
- Ses paramètres spécifiques
- Sa gestion des ressources (cabines/positions)

=============================================================================
                    TECHNOLOGIES UTILISÉES
=============================================================================

Backend     : Django 5.2, Python 3.13
Frontend    : Bootstrap 5, HTML5, JavaScript
Base données: SQLite (dev), PostgreSQL (prod recommandé)
Task Queue  : Celery (avec Redis en prod)
Formulaires : django-crispy-forms, crispy-bootstrap5
Filtres     : django-filter
Uploads     : Pillow (images)

=============================================================================
                      SÉCURITÉ & PRODUCTION
=============================================================================

IMPORTANT - AVANT DE DÉPLOYER EN PRODUCTION :

1. Changer SECRET_KEY (utiliser variables d'environnement)
2. Mettre DEBUG = False
3. Configurer ALLOWED_HOSTS
4. Migrer vers PostgreSQL
5. Configurer Celery avec Redis
6. Installer Gunicorn + Nginx
7. Activer HTTPS (certificat SSL)
8. Configurer les backups automatiques
9. Mettre en place le monitoring
10. Externaliser les fichiers média (S3/Azure)

Voir DEPLOYMENT.md pour le guide complet de déploiement.

=============================================================================
                      DOCUMENTATION
=============================================================================

README.md           : Documentation complète (format Markdown)
DEPLOYMENT.md       : Guide de déploiement en production
CONTRIBUTING.md     : Guide de contribution pour développeurs
.env.example        : Exemple de configuration environnement
VALIDATION.md       : Guide de validation des modifications

Documentation en ligne : [À venir]

=============================================================================
                      SUPPORT & CONTACT
=============================================================================

Pour toute question ou problème :
1. Consulter README.md (documentation détaillée)
2. Vérifier les logs : /var/log/girrex/ (production)
3. Lancer python check_code.py pour vérifier le code
4. Ouvrir une issue sur le repository

Email : [À définir]
Repository : [À définir]

=============================================================================
                         LICENCE
=============================================================================

Usage interne DGA Essais en Vol.
Tous droits réservés.

=============================================================================
                      NOTES DE VERSION
=============================================================================

VERSION 0.9 (Développement - Octobre 2025)
-------------------------------------------
✓ Architecture modulaire 10 applications
✓ Système de permissions avancé avec délégations
✓ Gestion RH complète
✓ Planning opérationnel avec versioning
✓ Gestion documentaire avec cycle de vie
✓ Module technique (pannes, MISO)
✓ Module QS (FNE)
✓ Module ES (études de sécurité)
✓ Module Cyber (SMSI)
✓ Module Compétences (MUA)
✓ Module Activités
✓ Module Feedback

À VENIR VERSION 1.0 (Production)
---------------------------------
- Tests complets (coverage > 70%)
- Optimisation performances
- Configuration production
- Documentation utilisateur
- Formation utilisateurs
- Mise en production pilote

=============================================================================
                      REMERCIEMENTS
=============================================================================

Développé pour la DGA Essais en Vol
Merci à tous les utilisateurs pilotes pour leurs retours

Technologies utilisées :
- Django Framework
- Bootstrap
- PostgreSQL
- Redis
- Nginx
- Et toute la communauté open source

=============================================================================

Pour démarrer rapidement :
  python manage.py runserver

Puis ouvrir : http://127.0.0.1:8000/

Bon développement ! 🚀

=============================================================================
