# 🏥 MODULE MÉDICAL - Guide complet

## 🎯 Ce que je dois savoir

Le module médical gère le suivi médical des agents et son intégration avec le système MUA (compétences).

**Localisation** : `core/` (fait partie du module core, pas un module séparé)

---

## 📐 ARCHITECTURE

### Modèles (core/models/medical.py)

```python
CertificatMed          # Certificat médical d'aptitude
RendezVousMedical      # RDV de visite médicale
HistoriqueRDV          # Traçabilité complète des RDV
ArretMaladie           # Arrêts maladie
CentreMedical          # Centres médicaux agréés
Notification           # Notifications système
```

### Vues (core/views/medical.py)

```python
# RDV
planifier_rdv_medical_view()
modifier_rdv_medical_view()
annuler_rdv_medical_view()
saisir_resultat_visite_view()
historique_rdv_view()

# Dossiers
dossier_medical_view()
dashboard_medical_centre_view()
dashboard_medical_national_view()

# Arrêts
declarer_arret_maladie_view()

# Fonction utile
peut_voir_dossier_medical(request, agent_cible)  # Pattern de vérification d'accès
```

---

## 🔄 WORKFLOW COMPLET

### 1. Planification d'un RDV

```
Agent OU FORM_LOCAL
    ↓
planifier_rdv_medical_view()
    ↓
RendezVousMedical créé (statut=PLANIFIE)
    ↓
HistoriqueRDV créé (action=CREATION)
```

**Code clé :**
```python
rdv = RendezVousMedical.objects.create(
    agent=agent,
    date_heure_rdv=date_rdv,
    organisme_medical=organisme,
    statut=RendezVousMedical.StatutRDV.PLANIFIE,
    created_by=request.user
)

HistoriqueRDV.objects.create(
    rdv=rdv,
    action=HistoriqueRDV.TypeAction.CREATION,
    utilisateur=request.user,
    nouveau_statut=rdv.statut,
    nouvelle_date=rdv.date_heure_rdv,
    commentaire=f"RDV planifié pour {agent.trigram}"
)
```

### 2. Saisie du résultat

```
Agent va au RDV
    ↓
Agent OU FORM_LOCAL saisit le résultat
    ↓
saisir_resultat_visite_view()
    ↓
CertificatMed créé (resultat=APTE/INAPTE)
    ↓
RDV.statut = REALISE
    ↓
HistoriqueRDV créé (action=REALISATION)
    ↓
⚠️ IMPACT SUR MUA (voir section ci-dessous)
```

**Code clé :**
```python
certificat = CertificatMed.objects.create(
    agent=agent,
    date_visite=rdv.date_heure_rdv.date(),
    resultat='APTE',  # ou INAPTE, INAPTE_TEMP
    date_expiration_aptitude=date_expiration,
    saisi_par=request.user
)

rdv.certificat_genere = certificat
rdv.statut = RendezVousMedical.StatutRDV.REALISE
rdv.save()
```

### 3. Impact sur le socle MUA

```
CertificatMed APTE créé
    ↓
Agent.certificat_medical_actif() retourne ce certificat
    ↓
competences.services.calculer_statut_socle(agent)
    ↓
Vérifie : Médical ✅ + Linguistique ? + RAF AERO ?
    ↓
Si TOUT valide → Socle valide → MUA peut être valide
```

**⚠️ IMPORTANT** : Le socle est **recalculé dynamiquement** à chaque consultation. Il n'y a **AUCUNE mise à jour automatique** de la MUA quand un certificat est créé.

---

## 🔗 INTÉGRATION AVEC MODULE COMPETENCES

### Lien critique : Socle de validité MUA

Le **socle de validité MUA** est calculé dans `competences/services.py` :

```python
def calculer_statut_socle(agent):
    """
    Vérifie les 3 éléments du socle.
    
    Returns:
        {
            'est_valide': bool,
            'motifs': [],
            'checklist': [
                {'nom': 'Aptitude Médicale', 'valide': True/False, 'details': '...'},
                {'nom': 'Aptitude Linguistique', 'valide': True/False, 'details': '...'},
                {'nom': 'Formation RAF AERO', 'valide': True/False, 'details': '...'}
            ]
        }
    """
    today = timezone.now().date()
    
    # 1. MÉDICAL
    certificat = CertificatMed.objects.filter(agent=agent).order_by('-date_visite').first()
    echeance_med = certificat.date_expiration_aptitude if certificat else None
    med_valide = certificat and echeance_med and echeance_med >= today
    
    # 2. LINGUISTIQUE
    mention_ling = MentionLinguistique.objects.filter(brevet__agent=agent, langue='ANGLAIS').first()
    echeance_ling = mention_ling.date_echeance if mention_ling else None
    ling_valide = mention_ling and echeance_ling and echeance_ling >= today
    
    # 3. RAF AERO
    raf_aero = SuiviFormationReglementaire.objects.filter(brevet__agent=agent, formation__slug='fh-raf-aero').first()
    echeance_raf = raf_aero.date_echeance if raf_aero else None
    raf_valide = raf_aero and echeance_raf and echeance_raf >= today
    
    socle_est_valide = med_valide and ling_valide and raf_valide
    
    return {
        'est_valide': socle_est_valide,
        'motifs': [...],
        'checklist': [...]
    }
```

### Utilisation du socle

```python
# Dans competences/services.py
def is_agent_apte_for_flux(agent, flux, on_date):
    """Vérifie si un agent peut contrôler."""
    # Étape 1: Vérifier le socle
    socle_context = calculer_statut_socle(agent)
    if not socle_context['est_valide']:
        return False, f"Socle invalide ({socle_context['motifs'][0]})"
    
    # Étape 2: Vérifier la MUA
    mua = MentionUniteAnnuelle.objects.get(...)
    if mua.statut != 'ACTIF':
        return False, "MUA non active"
    
    return True, ""
```

---

## 📊 DASHBOARDS MÉDICAUX

### Dashboard Centre

**URL** : `/medical/dashboard-centre/<centre_id>/`

**Accès** :
- Chef de Centre / Adjoint Chef de Centre : leur centre uniquement
- FORM_LOCAL : leur centre uniquement
- Chef de Division / Adjoint Chef Division : tous les centres

**Contenu** :
```python
{
    'alertes_critiques': [],      # Aucun certificat, INAPTE, expiré
    'alertes_urgentes': [],        # < 30 jours
    'alertes_importantes': [],     # 30-90 jours
    'agents_ok': [],               # > 90 jours
    'stats': {
        'total': int,
        'critiques': int,
        'urgentes': int,
        'importantes': int,
        'ok': int,
        'taux_conformite': float
    }
}
```

### Dashboard National

**URL** : `/medical/dashboard-national/`

**Accès** :
- Chef de Division
- Adjoint Chef de Division
- Adjoint Form

**Contenu** :
- Statistiques globales tous centres
- Répartition par centre
- Filtres (centre, statut, échéance)
- Liste des agents filtrés

---

## 🔐 PERMISSIONS

### Fonction de vérification d'accès

**⚠️ PATTERN IMPORTANT À RÉUTILISER** :

```python
def peut_voir_dossier_medical(request, agent_cible):
    """
    Vérifie si l'utilisateur peut voir le dossier médical de l'agent cible.
    Pattern réutilisable pour d'autres fonctionnalités similaires.
    """
    if not hasattr(request.user, 'agent_profile'):
        return False
    
    agent_user = request.user.agent_profile
    
    # 1. L'agent voit SON propre dossier
    if agent_user.id_agent == agent_cible.id_agent:
        return True
    
    # 2. Vision nationale (permission)
    if 'competences.view_all_licences' in request.effective_perms:
        return True
    
    # 3. Vision nationale (rôle explicite - défense en profondeur)
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
```

**Pourquoi double vérification (permission + rôle) ?**
- Défense en profondeur
- Au cas où la permission ne serait pas correctement assignée
- Garantit que les rôles nationaux ont TOUJOURS accès

### Matrice des accès

| Rôle | Dossier perso | Dossiers centre | Tous dossiers | Dashboard centre | Dashboard national |
|------|---------------|-----------------|---------------|------------------|-------------------|
| Agent | ✅ | ❌ | ❌ | ❌ | ❌ |
| FORM_LOCAL | ✅ | ✅ | ❌ | ✅ (son centre) | ❌ |
| Chef de Centre | ✅ | ✅ | ❌ | ✅ (son centre) | ❌ |
| Adjoint Chef Centre | ✅ | ✅ | ❌ | ✅ (son centre) | ❌ |
| Chef de Division | ✅ | ✅ | ✅ | ✅ (tous) | ✅ |
| Adjoint Chef Division | ✅ | ✅ | ✅ | ✅ (tous) | ✅ |
| Adjoint Form | ✅ | ✅ | ✅ | ✅ (tous) | ✅ |

---

## 📝 MODÈLES - DÉTAILS

### CertificatMed

**Champs importants** :
```python
agent = ForeignKey(Agent)
date_visite = DateField()
resultat = CharField(choices=['APTE', 'INAPTE', 'INAPTE_TEMP'])
date_expiration_aptitude = DateField()  # Obligatoire si APTE
restrictions = TextField(blank=True)
fichier_certificat = FileField(blank=True)  # Optionnel !
saisi_par = ForeignKey(User)  # Traçabilité
date_saisie = DateTimeField(auto_now_add=True)
```

**Properties utiles** :
```python
@property
def est_valide_aujourdhui(self):
    if not self.date_expiration_aptitude:
        return False
    return self.date_expiration_aptitude >= date.today()

@property
def jours_avant_expiration(self):
    if not self.date_expiration_aptitude:
        return None
    return (self.date_expiration_aptitude - date.today()).days
```

**Method sur Agent** :
```python
def certificat_medical_actif(self):
    """Retourne le certificat médical actif (le plus récent APTE et valide)."""
    return self.certificats_medicaux.filter(
        resultat='APTE',
        date_expiration_aptitude__gte=date.today()
    ).order_by('-date_visite').first()
```

### RendezVousMedical

**Statuts** :
```python
class StatutRDV(models.TextChoices):
    PLANIFIE = 'PLANIFIE', 'Planifié'
    REPORTE = 'REPORTE', 'Reporté'
    REALISE = 'REALISE', 'Réalisé'
    ANNULE = 'ANNULE', 'Annulé'
```

**Champs de traçabilité** :
```python
created_by = ForeignKey(User, related_name='rdv_medicaux_crees')
modified_by = ForeignKey(User, related_name='rdv_medicaux_modifies')
date_creation = DateTimeField(auto_now_add=True)
date_modification = DateTimeField(auto_now=True)
```

### HistoriqueRDV

**⚠️ ESSENTIEL pour l'auditabilité** :

```python
class TypeAction(models.TextChoices):
    CREATION = 'CREATION', 'Création'
    MODIFICATION = 'MODIFICATION', 'Modification'
    ANNULATION = 'ANNULATION', 'Annulation'
    REALISATION = 'REALISATION', 'Réalisation'

rdv = ForeignKey(RendezVousMedical, related_name='historique')
action = CharField(choices=TypeAction.choices)
utilisateur = ForeignKey(User)
date_action = DateTimeField(auto_now_add=True)
ancien_statut = CharField(blank=True)
nouveau_statut = CharField(blank=True)
ancienne_date = DateTimeField(null=True)
nouvelle_date = DateTimeField(null=True)
commentaire = TextField(blank=True)
```

**Créer un historique** (à faire pour CHAQUE modification) :
```python
HistoriqueRDV.objects.create(
    rdv=rdv,
    action=HistoriqueRDV.TypeAction.MODIFICATION,
    utilisateur=request.user,
    ancien_statut=ancien_statut,
    nouveau_statut=nouveau_statut,
    ancienne_date=ancienne_date,
    nouvelle_date=nouvelle_date,
    commentaire="Description du changement"
)
```

---

## 🎨 UX - CODE COULEUR

### Statut médical

```python
# Dans la vue
statut_info = {
    'classe': 'success',              # Couleur header
    'badge_classe': 'bg-success',     # Couleur badge
    'libelle': 'APTE',
}

# Logique de couleur
if resultat == 'APTE':
    if jours_restants > 90:
        classe = 'success'  # Vert
    elif jours_restants > 30:
        classe = 'warning'  # Orange (header seulement)
    else:
        classe = 'danger'   # Rouge (header seulement)
    
    badge_classe = 'bg-success'  # Badge reste TOUJOURS vert si APTE
```

### Dashboard

- 🔴 **Critiques** : bg-danger (aucun certificat, INAPTE, expiré)
- 🟠 **Urgentes** : bg-warning (< 30 jours)
- 🟡 **Importantes** : bg-info (30-90 jours)
- ✅ **OK** : bg-success (> 90 jours)

---

## 🧪 TESTS À FAIRE

Si je modifie le module médical, tester :

1. **Workflow complet** :
   - Planifier RDV → Saisir résultat APTE → Vérifier socle MUA valide
   
2. **Permissions** :
   - Agent voit son dossier
   - FORM_LOCAL voit son centre
   - Chef Division voit tout
   
3. **Traçabilité** :
   - Chaque action crée un HistoriqueRDV
   
4. **Intégration MUA** :
   - Certificat APTE → Socle valide
   - Certificat expiré → Socle invalide

---

## 📚 VOIR AUSSI

- `ARCHITECTURE.md` : Vue d'ensemble
- `PERMISSIONS.md` : Système de permissions
- `MODULES.md` : Lien avec module competences
- `CONVENTIONS.md` : Conventions de code

---

*Ce module est crucial car il impacte directement la validité des MUA.*

*Janvier 2025*
