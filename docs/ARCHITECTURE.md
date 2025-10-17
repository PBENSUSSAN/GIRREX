# 🏗️ ARCHITECTURE GIRREX

## 📌 Vue d'ensemble

GIRREX est une application Django modulaire pour la gestion des opérations d'un centre de contrôle aérien.

**Stack technique :**
- Django 5.1+
- Python 3.13+
- PostgreSQL (production) / SQLite (dev)
- Bootstrap 5 + Bootstrap Icons
- Celery + Redis (tâches asynchrones)

---

## 📦 STRUCTURE DES MODULES

```
GIRREX/
├── girrex_project/          # Configuration Django principale
│   ├── settings.py          # Paramètres (JAMAIS modifier INSTALLED_APPS sans raison)
│   ├── urls.py              # Routes principales
│   └── middleware.py        # Middleware permissions (⚠️ NE PAS TOUCHER)
├── core/                    # Module principal (RH, médical, notifications)
├── competences/             # Gestion des compétences et MUA
├── activites/               # Planification et saisie activités
├── qs/                      # Qualité et Sécurité aérienne
├── cyber/                   # Cybersécurité (SMSI)
├── es/                      # Études de Sécurité
├── technique/               # Gestion technique (pannes, MISO)
├── documentation/           # Gestion documentaire (app Django)
├── feedback/                # Retours utilisateurs
├── suivi/                   # Suivi des actions
└── templates/               # Templates globaux
```

---

## ⚠️ RÈGLES CRITIQUES - À RESPECTER ABSOLUMENT

### 🔴 **NE JAMAIS TOUCHER AU SYSTÈME DE PERMISSIONS**

Le système de permissions est complexe et fragile. **Toute modification peut casser l'ensemble de l'application.**

**Ce qui est INTERDIT :**
- ❌ Modifier `core/middleware.py` (calcul des permissions effectives)
- ❌ Changer les noms de groupes Django existants
- ❌ Modifier les permissions dans `core/models/parametrage.py` (Role, AgentRole)
- ❌ Toucher aux attributs `request.effective_perms`, `request.active_agent_role`, `request.centre_agent`
- ❌ Créer des vérifications de permissions custom sans passer par `effective_perms`

**Ce qui est AUTORISÉ :**
- ✅ Utiliser `request.effective_perms` pour vérifier les permissions
- ✅ Utiliser les décorateurs existants (`@effective_permission_required`)
- ✅ Vérifier le rôle via `request.active_agent_role.role.nom`

**Exemple correct de vérification de permission :**
```python
def ma_vue(request):
    # ✅ BON
    if 'competences.view_all_licences' in request.effective_perms:
        # L'utilisateur a la permission
        pass
    
    # ✅ BON
    if request.active_agent_role and request.active_agent_role.role.nom == Role.RoleName.CHEF_DE_DIVISION:
        # L'utilisateur a ce rôle
        pass
    
    # ❌ MAUVAIS - Ne jamais faire ça
    if request.user.has_perm('competences.view_all_licences'):
        # Cette approche contourne le middleware !
        pass
```

---

## 🔐 SYSTÈME DE PERMISSIONS (Vue simplifiée)

### Hiérarchie des rôles

```
NATIONAL (vision sur tous les centres)
├── Chef de Division
├── Adjoint Chef de Division
└── Adjoint Form

LOCAL (vision sur UN centre)
├── Chef de Centre
├── Adjoint Chef de Centre
├── FORM_LOCAL
├── Chef de Quart
└── Contrôleur

DOMAINES
├── Responsable SMS / SMS Local
├── QS Local
├── ES Local
└── SMSI Local
```

### Permissions calculées dynamiquement

Le middleware `RolePermissionMiddleware` calcule :
- `request.effective_perms` : Permissions effectives (basées sur le rôle actif)
- `request.active_agent_role` : Rôle actuellement actif
- `request.centre_agent` : Centre de rattachement

**⚠️ Ces attributs sont recalculés à chaque requête. Ne jamais les modifier.**

---

## 🏛️ MODÈLES PRINCIPAUX

### Core (RH)
- `Agent` : Données d'un agent (trigram, nom, centre, actif)
- `Centre` : Centre de contrôle
- `Role` : Rôles métier (Chef de Centre, FORM_LOCAL, etc.)
- `AgentRole` : Attribution d'un rôle à un agent

### Core (Médical)
- `CertificatMed` : Certificats médicaux
- `RendezVousMedical` : RDV médicaux
- `HistoriqueRDV` : Traçabilité des RDV
- `ArretMaladie` : Arrêts maladie

### Compétences
- `Brevet` : Brevets ATC
- `Qualification` : Qualifications d'un agent
- `MentionUniteAnnuelle` (MUA) : Contrat annuel de contrôle
- `MentionLinguistique` : Mentions linguistiques
- `SuiviFormationReglementaire` : Formations obligatoires (RAF AERO, etc.)

### Activités
- `Vol` : Vol enregistré
- `SaisieActivite` : Activité d'un agent sur un vol

---

## 🎯 PRINCIPES DE DÉVELOPPEMENT

### 1. Toujours utiliser le middleware de permissions
```python
# Dans une vue
@login_required
def ma_vue(request):
    if 'mon_app.ma_permission' not in request.effective_perms:
        raise PermissionDenied("Accès refusé")
```

### 2. Respecter la séparation des responsabilités
- **Models** : Logique métier, properties, méthodes
- **Views** : Logique de présentation, gestion HTTP
- **Services** : Logique complexe réutilisable (ex: `competences/services.py`)
- **Templates** : Affichage uniquement

### 3. Nommer correctement
- Vues : `nom_action_view` (ex: `planifier_rdv_medical_view`)
- URLs : `nom-action` (ex: `planifier-rdv-medical`)
- Templates : `app/nom_action.html`

### 4. Toujours tracer les modifications importantes
```python
# Exemple avec HistoriqueRDV
HistoriqueRDV.objects.create(
    rdv=rdv,
    action=HistoriqueRDV.TypeAction.MODIFICATION,
    utilisateur=request.user,
    ancien_statut=ancien_statut,
    nouveau_statut=nouveau_statut,
    commentaire="Description du changement"
)
```

---

## 📚 FICHIERS DE DOCUMENTATION

- `ARCHITECTURE.md` ← Vous êtes ici
- `MODULES.md` : Description détaillée de chaque module
- `PERMISSIONS.md` : Détail complet du système de permissions
- `DATABASE.md` : Schéma de la base de données
- `CONVENTIONS.md` : Conventions de code
- `MODULE_MEDICAL.md` : Documentation du module médical

---

## 🆘 EN CAS DE PROBLÈME

**Si l'application ne fonctionne plus après vos modifications :**

1. Vérifiez que vous n'avez PAS touché au middleware
2. Vérifiez que les permissions sont bien vérifiées via `request.effective_perms`
3. Vérifiez les logs Django
4. Consultez le fichier `PERMISSIONS.md` pour comprendre le système

**Besoin d'ajouter une nouvelle fonctionnalité ?**
1. Lisez d'abord `CONVENTIONS.md`
2. Regardez comment les modules existants fonctionnent
3. Ne touchez JAMAIS aux permissions sans consulter `PERMISSIONS.md`

---

*Documentation créée : Janvier 2025*
*Dernière mise à jour : Janvier 2025*
