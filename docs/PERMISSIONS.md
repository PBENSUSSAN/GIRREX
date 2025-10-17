# 🔐 SYSTÈME DE PERMISSIONS GIRREX

## ⚠️ AVERTISSEMENT CRITIQUE

**CE SYSTÈME NE DOIT JAMAIS ÊTRE MODIFIÉ SANS UNE COMPRÉHENSION TOTALE DE SON FONCTIONNEMENT.**

Toute modification du système de permissions peut casser l'ensemble de l'application et créer des failles de sécurité graves.

---

## 📋 PRINCIPE GÉNÉRAL

GIRREX utilise un système de permissions **à deux niveaux** :

1. **Permissions Django** (techniques) : Groupes et permissions standard
2. **Rôles métier** (fonctionnels) : Rôles avec scope (national, local, opérationnel)

Le middleware `RolePermissionMiddleware` fait le lien entre les deux.

---

## 🏗️ ARCHITECTURE DU SYSTÈME

### 1. Modèle `Role` (core/models/parametrage.py)

```python
class Role(models.Model):
    class RoleName(models.TextChoices):
        CHEF_DE_DIVISION = 'CHEF_DE_DIVISION', 'Chef de Division'
        ADJOINT_CHEF_DE_DIVISION = 'ADJOINT_CHEF_DE_DIVISION', 'Adjoint Chef de Division'
        ADJOINT_FORM = 'ADJOINT_FORM', 'Adjoint Form'
        CHEF_DE_CENTRE = 'CHEF_DE_CENTRE', 'Chef de Centre'
        # ... autres rôles
    
    class RoleScope(models.TextChoices):
        CENTRAL = 'CENTRAL', 'Central'        # Vision nationale
        LOCAL = 'LOCAL', 'Local'              # Vision centre
        OPERATIONNEL = 'OPERATIONNEL', 'Opérationnel'
    
    nom = models.CharField(max_length=50, choices=RoleName.choices)
    groups = models.ManyToManyField(Group)  # Groupes Django liés
    scope = models.CharField(max_length=20, choices=RoleScope.choices)
```

### 2. Modèle `AgentRole`

Attribue un rôle à un agent (avec centre si local/opérationnel) :

```python
class AgentRole(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    centre = models.ForeignKey(Centre, null=True, blank=True)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
```

### 3. Middleware `RolePermissionMiddleware`

**⚠️ NE JAMAIS MODIFIER CE FICHIER : `girrex_project/middleware.py`**

Le middleware ajoute à chaque requête :
- `request.effective_perms` : Set des permissions effectives
- `request.active_agent_role` : Rôle actif (AgentRole)
- `request.centre_agent` : Centre de l'agent
- `request.is_supervisor_view` : Boolean (vue supervision)
- `request.show_operational_view` : Boolean (vue opérationnelle)

---

## 🎭 LISTE DES RÔLES ET LEURS PERMISSIONS

### Rôles NATIONAUX (scope=CENTRAL)

#### Chef de Division
- **Scope** : National (tous les centres)
- **Permissions** : `competences.view_all_licences`, `competences.change_licence`, etc.
- **Accès** : Tous les dashboards, toutes les données

#### Adjoint Chef de Division
- **Scope** : National
- **Permissions** : Identiques à Chef de Division

#### Adjoint Form
- **Scope** : National
- **Permissions** : `competences.view_all_licences`
- **Accès** : Vue nationale des compétences et médical

---

### Rôles LOCAUX (scope=LOCAL)

#### Chef de Centre
- **Scope** : Son centre uniquement
- **Permissions** : `core.change_centre`, consultation de son centre
- **Accès** : Dashboard médical de son centre, gestion capacité

#### Adjoint Chef de Centre
- **Scope** : Son centre uniquement
- **Permissions** : Identiques à Chef de Centre

#### FORM_LOCAL
- **Scope** : Son centre uniquement
- **Permissions** : `competences.change_licence` (sur son centre)
- **Accès** : Gestion compétences, planification RDV médicaux pour agents du centre

---

### Rôles OPÉRATIONNELS (scope=OPERATIONNEL)

#### Chef de Quart
- **Scope** : Son centre, opérations quotidiennes
- **Permissions** : `core.open_close_service`, `core.change_feuilletemps`
- **Accès** : Ouvrir/fermer service, saisir activités, feuille d'heures

#### Contrôleur
- **Scope** : Son centre
- **Permissions** : Basiques
- **Accès** : Consulter son dossier, planifier ses RDV médicaux

---

## 🔧 COMMENT UTILISER LES PERMISSIONS

### ✅ MÉTHODE CORRECTE (toujours utiliser)

```python
from django.core.exceptions import PermissionDenied

@login_required
def ma_vue(request):
    # Vérifier une permission
    if 'competences.view_all_licences' not in request.effective_perms:
        raise PermissionDenied("Vous n'avez pas accès à cette ressource.")
    
    # Vérifier un rôle
    if request.active_agent_role and request.active_agent_role.role.nom == Role.RoleName.CHEF_DE_DIVISION:
        # Logique spécifique au Chef de Division
        pass
    
    # Vérifier le centre
    if request.centre_agent:
        agents_du_centre = Agent.objects.filter(centre=request.centre_agent)
```

### ❌ MÉTHODES INCORRECTES (ne JAMAIS utiliser)

```python
# ❌ MAUVAIS - Contourne le middleware
if request.user.has_perm('competences.view_all_licences'):
    pass

# ❌ MAUVAIS - Vérifie les groupes directement
if request.user.groups.filter(name='FORM').exists():
    pass

# ❌ MAUVAIS - Modifie les attributs calculés
request.effective_perms.add('nouvelle_permission')  # NE JAMAIS FAIRE ÇA
```

---

## 🛡️ PATTERN DE VÉRIFICATION D'ACCÈS

### Pour une vue avec accès à un agent spécifique

```python
def peut_voir_dossier_medical(request, agent_cible):
    """
    Exemple de fonction réutilisable pour vérifier l'accès.
    """
    if not hasattr(request.user, 'agent_profile'):
        return False
    
    agent_user = request.user.agent_profile
    
    # 1. L'agent voit SON propre dossier
    if agent_user.id_agent == agent_cible.id_agent:
        return True
    
    # 2. Vision nationale (Chef Division, Adjoint Form, etc.)
    if 'competences.view_all_licences' in request.effective_perms:
        return True
    
    # 3. Vérification explicite par rôle (défense en profondeur)
    if request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_CHEF_DE_DIVISION,
        Role.RoleName.ADJOINT_FORM
    ]:
        return True
    
    # 4. FORM_LOCAL voit son centre
    if 'competences.change_licence' in request.effective_perms:
        if request.centre_agent and agent_cible.centre:
            if request.centre_agent.id == agent_cible.centre.id:
                return True
    
    # 5. Chef de Centre voit son centre
    if request.active_agent_role and request.active_agent_role.role.nom in [
        Role.RoleName.CHEF_DE_CENTRE,
        Role.RoleName.ADJOINT_CHEF_DE_CENTRE
    ]:
        if request.centre_agent and agent_cible.centre:
            if request.centre_agent.id == agent_cible.centre.id:
                return True
    
    return False

# Utilisation dans une vue
@login_required
def dossier_medical_view(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    
    if not peut_voir_dossier_medical(request, agent):
        raise PermissionDenied("Accès refusé.")
    
    # Suite de la vue...
```

---

## 📝 PERMISSIONS DJANGO STANDARD

### Groupes utilisés

- **FORM** : Formateurs (nationaux et locaux)
- **CDC** : Chefs de Centre
- **CDQ** : Chefs de Quart
- **SMS** : Responsables SMS
- **QS** : Responsables QS
- **ES** : Responsables ES

### Permissions par app

**core :**
- `core.open_close_service` : Ouvrir/fermer le service
- `core.change_feuilletemps` : Modifier feuille de temps
- `core.change_centre` : Gérer un centre

**competences :**
- `competences.view_all_licences` : Vision nationale des compétences
- `competences.change_licence` : Modifier compétences (FORM_LOCAL)

---

## 🚨 QUE FAIRE SI VOUS DEVEZ AJOUTER UNE PERMISSION

### Étape 1 : Créer la permission dans le modèle

```python
class Meta:
    permissions = [
        ("ma_nouvelle_permission", "Description de la permission"),
    ]
```

### Étape 2 : Créer une migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### Étape 3 : Assigner la permission au groupe

Via l'admin Django ou un script :

```python
from django.contrib.auth.models import Group, Permission

group = Group.objects.get(name='FORM')
permission = Permission.objects.get(codename='ma_nouvelle_permission')
group.permissions.add(permission)
```

### Étape 4 : Lier le groupe au rôle

Via l'admin Django : Modifier le rôle et ajouter le groupe.

### ⚠️ NE JAMAIS :
- Modifier directement le middleware
- Supprimer des permissions existantes
- Changer les noms des groupes existants

---

## 🔍 DEBUGGING DES PERMISSIONS

### Afficher les permissions d'un utilisateur

```python
# Dans une vue ou le shell Django
print("Permissions effectives :", request.effective_perms)
print("Rôle actif :", request.active_agent_role)
print("Centre :", request.centre_agent)
```

### Vérifier les permissions d'un rôle

```python
# Shell Django
from core.models import Role
role = Role.objects.get(nom='FORM_LOCAL')
print("Groupes :", role.groups.all())
for group in role.groups.all():
    print("Permissions du groupe :", group.permissions.all())
```

---

## 📚 VOIR AUSSI

- `ARCHITECTURE.md` : Vue d'ensemble du système
- `MODULES.md` : Description des modules
- `MODULE_MEDICAL.md` : Exemple d'utilisation des permissions

---

*⚠️ En cas de doute sur une modification du système de permissions, NE RIEN FAIRE et consulter la documentation existante.*

*Documentation créée : Janvier 2025*
