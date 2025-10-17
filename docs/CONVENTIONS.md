# 📐 CONVENTIONS DE CODE GIRREX

## 🎯 Pourquoi ce fichier existe

Pour que je code de manière cohérente avec l'existant. Ces conventions sont déjà appliquées dans tout le projet.

---

## 📁 STRUCTURE DES FICHIERS

### Organisation d'une app Django

```
mon_app/
├── models/
│   ├── __init__.py          # Importe tous les modèles
│   ├── model1.py
│   └── model2.py
├── views/
│   ├── __init__.py          # Importe toutes les vues
│   ├── gestion.py
│   └── consultation.py
├── migrations/
├── templates/
│   └── mon_app/
│       ├── liste.html
│       └── detail.html
├── admin.py
├── apps.py
├── forms.py
├── services.py              # Logique métier réutilisable
├── urls.py
└── tests.py
```

### Quand créer un `services.py`

✅ **Créer un `services.py` si :**
- Logique métier complexe utilisée par plusieurs vues
- Calculs lourds ou algorithmes
- Fonctions réutilisables entre modules

✅ **Exemple** : `competences/services.py`
```python
def calculer_statut_socle(agent):
    """Vérifie le socle de validité d'un agent."""
    # Logique complexe réutilisée partout
```

❌ **Ne pas créer de services.py si :**
- Simple CRUD
- Logique triviale (peut aller dans la vue)

---

## 🏗️ CONVENTIONS DE NOMMAGE

### Modèles

```python
# Nom : SingulierPascalCase
class Agent(models.Model):
    pass

class CertificatMed(models.Model):
    pass

class MentionUniteAnnuelle(models.Model):
    # Nom de table auto : mon_app_mentionuniteannuelle
    
    class Meta:
        verbose_name = "Mention d'Unité Annuelle (MUA)"
        verbose_name_plural = "Mentions d'Unité Annuelles (MUA)"
```

**Choix des champs :**
- `id_agent` au lieu de `id` quand c'est la PK (pour clarté)
- `date_creation` / `date_modification` pour traçabilité
- `created_by` / `modified_by` (ForeignKey User) pour audit
- `actif` (BooleanField) pour soft delete

### Vues

```python
# Nom : action_objet_view
def planifier_rdv_medical_view(request):
    pass

def modifier_rdv_medical_view(request, rdv_id):
    pass

def dashboard_medical_centre_view(request, centre_id):
    pass
```

**Pattern de vue :**
```python
@login_required
def ma_vue(request, objet_id):
    # 1. Récupérer l'objet
    objet = get_object_or_404(MonModele, pk=objet_id)
    
    # 2. Vérifier les permissions
    if 'mon_app.ma_permission' not in request.effective_perms:
        raise PermissionDenied("Message clair")
    
    # 3. Logique métier (ou appel service)
    if request.method == 'POST':
        form = MonForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            instance.save()
            messages.success(request, "Message de succès")
            return redirect('nom-url', objet_id=objet.id)
    else:
        form = MonForm()
    
    # 4. Préparer le contexte
    context = {
        'objet': objet,
        'form': form,
        'titre': "Titre de la page",
    }
    
    # 5. Render
    return render(request, 'mon_app/template.html', context)
```

### URLs

```python
# urls.py - Nom en kebab-case
urlpatterns = [
    path('rdv/planifier/', planifier_rdv_medical_view, name='planifier-rdv-medical'),
    path('rdv/<int:rdv_id>/modifier/', modifier_rdv_medical_view, name='modifier-rdv-medical'),
    path('dashboard/centre/<int:centre_id>/', dashboard_medical_centre_view, name='dashboard-medical-centre'),
]
```

**Convention noms d'URL :**
- `action-objet` : `planifier-rdv`, `modifier-agent`
- `objet-action` si plus logique : `dossier-medical`, `dashboard-centre`

### Templates

```
templates/
├── base.html                    # Template principal
├── partials/
│   ├── sidebar_menu.html        # Menu latéral
│   └── breadcrumb.html
├── mon_app/
│   ├── liste_objets.html
│   ├── detail_objet.html
│   └── form_objet.html          # Utilisé pour créer ET modifier
```

**Nommage templates :**
- `liste_*.html` : Liste d'objets
- `detail_*.html` : Détail d'un objet
- `form_*.html` : Formulaire (création/modification)
- `dashboard_*.html` : Tableaux de bord

---

## 🎨 CONVENTIONS TEMPLATE

### Extends et blocks

```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Titre de la page{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <!-- Contenu -->
</div>
{% endblock %}
```

### Variables de contexte standards

```python
context = {
    'titre': "Titre affiché en h2",          # Toujours présent
    'agent_concerne': agent,                  # Si page concerne un agent
    'centre': centre,                         # Si page concerne un centre
    'objet': objet_principal,                 # Objet principal de la page
}
```

### Messages Django

```python
from django.contrib import messages

# Types de messages
messages.success(request, "Opération réussie.")
messages.warning(request, "Attention : ...")
messages.error(request, "Erreur : ...")
messages.info(request, "Information : ...")
```

**Dans le template :**
```django
{% if messages %}
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endfor %}
{% endif %}
```

---

## 🗃️ CONVENTIONS BASE DE DONNÉES

### Relations

```python
# ForeignKey : TOUJOURS avec related_name explicite
agent = models.ForeignKey(
    Agent, 
    on_delete=models.CASCADE,
    related_name='certificats_medicaux'  # ✅
)

# ManyToMany : related_name au pluriel
centres = models.ManyToManyField(
    Centre,
    related_name='regles_renouvellement'
)
```

### Dates et traçabilité

```python
class MonModele(models.Model):
    # Dates de gestion
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    # Traçabilité utilisateur
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='%(class)s_crees'
    )
    modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='%(class)s_modifies'
    )
```

### Choices

```python
class MonModele(models.Model):
    class StatutChoices(models.TextChoices):
        EN_COURS = 'EN_COURS', 'En cours'
        TERMINE = 'TERMINE', 'Terminé'
        ANNULE = 'ANNULE', 'Annulé'
    
    statut = models.CharField(
        max_length=20,
        choices=StatutChoices.choices,
        default=StatutChoices.EN_COURS
    )
```

### Properties utiles

```python
class CertificatMed(models.Model):
    date_expiration_aptitude = models.DateField()
    
    @property
    def est_valide_aujourdhui(self):
        """Property pour vérification simple."""
        if not self.date_expiration_aptitude:
            return False
        return self.date_expiration_aptitude >= date.today()
    
    @property
    def jours_avant_expiration(self):
        """Retourne le nombre de jours avant expiration."""
        if not self.date_expiration_aptitude:
            return None
        return (self.date_expiration_aptitude - date.today()).days
```

---

## 🔐 PERMISSIONS - RAPPEL

### ✅ TOUJOURS faire

```python
# Vérifier via effective_perms
if 'mon_app.ma_permission' in request.effective_perms:
    # OK
    pass

# Vérifier le rôle si nécessaire
if request.active_agent_role and request.active_agent_role.role.nom == Role.RoleName.CHEF_DE_CENTRE:
    # OK
    pass
```

### ❌ JAMAIS faire

```python
# ❌ Contourne le middleware
if request.user.has_perm('mon_app.ma_permission'):
    pass

# ❌ Vérifie les groupes directement
if request.user.groups.filter(name='FORM').exists():
    pass
```

---

## 📝 DOCUMENTATION DU CODE

### Docstrings

```python
def ma_fonction(agent, date_debut, date_fin):
    """
    Calcule les heures de contrôle d'un agent sur une période.
    
    Args:
        agent (Agent): Agent concerné
        date_debut (date): Date de début de période
        date_fin (date): Date de fin de période
    
    Returns:
        dict: Dictionnaire avec les heures par flux
              {'cam': 50.5, 'cag_acs': 30.0, ...}
    
    Raises:
        ValueError: Si date_fin < date_debut
    """
    pass
```

### Commentaires dans le code

```python
# ✅ BON : Explique POURQUOI, pas QUOI
# On vérifie le socle AVANT la MUA car sans socle valide, 
# la MUA ne peut pas être valide même avec les heures
if not socle_est_valide:
    return False

# ❌ MAUVAIS : Répète le code
# On vérifie si le socle est valide
if not socle_est_valide:
    return False
```

---

## 🎨 CONVENTIONS FRONT-END

### Bootstrap 5

```html
<!-- Card standard -->
<div class="card shadow-sm mb-4">
    <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Titre</h5>
    </div>
    <div class="card-body">
        <!-- Contenu -->
    </div>
</div>

<!-- Boutons -->
<a href="{% url 'mon-url' %}" class="btn btn-primary">
    <i class="bi bi-plus-circle"></i> Ajouter
</a>
<button type="submit" class="btn btn-success">
    <i class="bi bi-check-circle"></i> Valider
</button>
```

### Bootstrap Icons

```html
<i class="bi bi-person"></i>           <!-- Personne -->
<i class="bi bi-house"></i>            <!-- Maison -->
<i class="bi bi-calendar"></i>         <!-- Calendrier -->
<i class="bi bi-heart-pulse"></i>      <!-- Médical -->
<i class="bi bi-eye"></i>              <!-- Voir -->
<i class="bi bi-pencil"></i>           <!-- Modifier -->
<i class="bi bi-trash"></i>            <!-- Supprimer -->
```

### Classes utilitaires courantes

```html
<!-- Marges -->
<div class="mt-4 mb-4">...</div>          <!-- Margin top/bottom 4 -->
<div class="ms-2 me-2">...</div>          <!-- Margin start/end 2 -->

<!-- Texte -->
<p class="text-muted">...</p>             <!-- Texte grisé -->
<strong class="text-danger">...</strong>   <!-- Texte rouge en gras -->

<!-- Couleurs de fond -->
<div class="bg-success text-white">...</div>
<div class="bg-warning text-dark">...</div>
<div class="bg-danger text-white">...</div>

<!-- Badges -->
<span class="badge bg-success">Valide</span>
<span class="badge bg-danger">Invalide</span>
```

---

## 🧪 TESTS

### Nommage des tests

```python
# tests.py
class AgentModelTest(TestCase):
    def test_agent_creation(self):
        """Test la création d'un agent."""
        pass
    
    def test_certificat_medical_actif(self):
        """Test la méthode certificat_medical_actif()."""
        pass
```

### Pattern de test

```python
def test_mon_cas(self):
    # Arrange : Préparer les données
    agent = Agent.objects.create(...)
    
    # Act : Exécuter l'action
    resultat = agent.certificat_medical_actif()
    
    # Assert : Vérifier le résultat
    self.assertIsNotNone(resultat)
    self.assertEqual(resultat.resultat, 'APTE')
```

---

## 🔄 GIT

### Messages de commit

```bash
# Format : type: description courte

# Types principaux
feat: nouvelle fonctionnalité
fix: correction de bug
refactor: refactorisation sans changement fonctionnel
docs: documentation
style: formatage, pas de changement de code
test: ajout/modification de tests

# Exemples
git commit -m "feat: ajout dashboard médical national"
git commit -m "fix: correction 403 pour Chef Division sur dossiers agents"
git commit -m "refactor: extraction logique médical vers services.py"
```

---

## 📚 EN CAS DE DOUTE

1. **Regarder le code existant** : Comment c'est fait ailleurs ?
2. **Lire `ARCHITECTURE.md`** : Comprendre la structure globale
3. **Lire `PERMISSIONS.md`** : Si c'est lié aux permissions
4. **Lire `MODULES.md`** : Comprendre le module concerné

---

*Ces conventions sont appliquées dans tout le projet. Les respecter garantit la cohérence.*

*Janvier 2025*
