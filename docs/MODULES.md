# 📦 MODULES GIRREX

## 🎯 Ce que je dois savoir rapidement

Chaque module = une app Django avec sa responsabilité. Voici ce que je dois chercher dans chaque module pour comprendre son fonctionnement.

---

## 🏛️ CORE - Le socle central

**Responsabilité** : RH, médical, notifications, paramétrage système

### Fichiers clés
- `models/rh.py` : Agent, Centre, Role, AgentRole, Delegation
- `models/medical.py` : CertificatMed, RendezVousMedical, HistoriqueRDV, ArretMaladie
- `models/parametrage.py` : Parametre, ValeurParametre, Role (⚠️ NE PAS TOUCHER)
- `views/medical.py` : Toutes les vues médicales
- `middleware.py` : ⚠️ **NE JAMAIS TOUCHER** - Calcul des permissions

### Concepts importants
- **Agent** : `id_agent` (PK), `trigram`, `centre`, `actif`, `user` (OneToOne)
- **CertificatMed** : `resultat` (APTE/INAPTE), `date_expiration_aptitude`, properties : `est_valide_aujourdhui`, `jours_avant_expiration`
- **HistoriqueRDV** : Traçabilité complète des RDV (qui a fait quoi, quand)

### Fonction utile
```python
def peut_voir_dossier_medical(request, agent_cible):
    # Pattern de vérification d'accès - réutilisable partout
    # Vérifie : agent lui-même, vision nationale, FORM_LOCAL du centre, Chef de Centre
```

### URLs principales
- `/medical/dossier/<agent_id>/` : Dossier médical d'un agent
- `/medical/dashboard-centre/<centre_id>/` : Dashboard médical centre
- `/medical/dashboard-national/` : Dashboard national

---

## 🎓 COMPETENCES - Gestion des compétences ATC

**Responsabilité** : Brevets, qualifications, MUA, mentions linguistiques, formations réglementaires

### Fichiers clés
- `models/brevet.py` : Brevet (licence ATC)
- `models/qualification.py` : Qualification (compétence sur un centre)
- `models/mua.py` : MentionUniteAnnuelle (contrat annuel de contrôle)
- `services.py` : ⚠️ **IMPORTANT** - Logique métier complexe

### Concepts CRITIQUES

#### MUA (Mention d'Unité Annuelle)
C'est le **"contrat annuel"** qui donne le droit de contrôler.

**Validité MUA** = **SOCLE valide** + **Heures valides**

**SOCLE DE VALIDITÉ** (calculé dans `services.calculer_statut_socle`) :
1. ✅ Aptitude médicale valide (CertificatMed APTE non expiré)
2. ✅ Mention linguistique anglais valide
3. ✅ Formation RAF AERO valide (tous les 3 ans)

Si **UN SEUL élément du socle est invalide → MUA INVALIDE**

```python
# services.py - Fonction critique
def calculer_statut_socle(agent):
    """
    Retourne : {'est_valide': bool, 'motifs': [], 'checklist': []}
    """
    # Vérifie les 3 éléments du socle
    # Utilisé partout où on vérifie si un agent peut contrôler
```

#### Workflow MUA
```
Agent → Certificat médical APTE → Socle valide
                                        ↓
                                    MUA valide si heures OK
```

### Services à utiliser
- `calculer_statut_socle(agent)` : Vérifie le socle d'un agent
- `get_mua_dossier_context(mua)` : Toutes les données pour afficher une MUA
- `is_agent_apte_for_flux(agent, flux, on_date)` : Vérifie si agent peut contrôler

### URLs principales
- `/competences/dossier/<agent_id>/` : Dossier de compétences
- `/competences/mua/<mua_id>/` : Détail d'une MUA
- `/competences/tableau-bord/` : Vue d'ensemble des compétences

---

## ✈️ ACTIVITES - Planification et saisie des vols

**Responsabilité** : Planification CCA, saisie activités de vol, relevés mensuels

### Fichiers clés
- `models.py` : Vol, SaisieActivite, Flux, CCA
- `views/cca_planning.py` : Planification J+1
- `views/saisie.py` : Saisie des activités

### Concepts importants
- **Vol** : Un vol réel avec `date_vol`, `duree_reelle`, `flux`, `centre`
- **SaisieActivite** : Activité d'un agent sur un vol (`role`, `agent`, `vol`)
- **Flux** : CAM, CAG_ACS, CAG_APS, TOUR

### Lien avec MUA
Les heures saisies dans SaisieActivite alimentent automatiquement les compteurs de la MUA de l'agent.

---

## 🛡️ QS - Qualité et Sécurité aérienne

**Responsabilité** : Gestion des FNE (Fiches de Notification d'Événement)

### Fichiers clés
- `models.py` : FNE, ClassificationFNE
- `views/` : Déclaration et suivi FNE

### Workflow FNE
```
Déclaration → Pré-classification → Classification définitive → Clôture
```

---

## 🔒 CYBER - Cybersécurité SMSI

**Responsabilité** : Pilotage du Système de Management de la Sécurité de l'Information

### Fichiers clés
- `models.py` : Risque, MesureSecurite, Incident
- `views/` : Dashboard SMSI, gestion des risques

### Accès
- **Relais Local** : Gère le SMSI de son centre
- **Central** : Vision nationale

---

## 📊 ES - Études de Sécurité

**Responsabilité** : Gestion des études de sécurité et changements

### Fichiers clés
- `models.py` : EtudeSécurité, Changement
- `views/` : Tableau des ES, classification des changements

---

## 🔧 TECHNIQUE - Maintenance technique

**Responsabilité** : Pannes, MISO (Mise en/hors Service d'Équipement)

### Fichiers clés
- `models.py` : Panne, MISO, Equipement
- `views/` : Signalement pannes, gestion MISO

---

## 📄 DOCUMENTATION - Gestion documentaire

**Responsabilité** : Base documentaire, versions, validations

### Fichiers clés
- `models.py` : Document, VersionDocument, TypeDocument
- `views/` : Consultation, upload, validation documents

---

## 💬 FEEDBACK - Retours utilisateurs

**Responsabilité** : Suggestions, bugs, améliorations

### Fichiers clés
- `models.py` : Feedback, CommentaireFeedback
- `views/` : Soumission, tableau de bord

---

## 📋 SUIVI - Tableau de suivi des actions

**Responsabilité** : Actions transverses, suivi, tableaux de bord

### Fichiers clés
- `models.py` : Action, CommentaireAction
- `views/` : Tableau de suivi multi-domaines

---

## 🔗 LIENS ENTRE MODULES

### Module MEDICAL → Module COMPETENCES
```
CertificatMed (APTE) → calculer_statut_socle() → MUA valide/invalide
```

**Quand l'agent saisit un certificat APTE :**
1. Le certificat est créé dans `core.CertificatMed`
2. `competences.services.calculer_statut_socle(agent)` est appelé (à la demande)
3. Si socle valide + heures OK → MUA reste valide
4. Aucune mise à jour automatique de la MUA (recalcul dynamique à chaque consultation)

### Module ACTIVITES → Module COMPETENCES
```
SaisieActivite (heures) → Agrégation → Compteurs MUA
```

Les heures de contrôle saisies alimentent les compteurs de la MUA pour la période en cours.

---

## 🎯 PATTERN DE DÉVELOPPEMENT

### Quand je dois ajouter une fonctionnalité

1. **Identifier le module** : Où dois-je coder ?
2. **Vérifier les services existants** : Y a-t-il déjà une fonction réutilisable ?
3. **Respecter l'architecture** :
   - Logique métier → `services.py` ou methods du modèle
   - Logique de présentation → `views/`
   - Requêtes complexes → managers ou querysets custom
4. **Permissions** : Toujours via `request.effective_perms`
5. **Traçabilité** : Si modification importante, créer un historique

### Quand je dois comprendre une fonctionnalité existante

1. **Lire le modèle** : Comprendre les champs, les relations, les properties
2. **Lire le service** (si existe) : Logique métier
3. **Lire la vue** : Comment c'est présenté
4. **Tester** : Créer un agent de test et essayer

---

## 📚 VOIR AUSSI

- `ARCHITECTURE.md` : Vue d'ensemble
- `PERMISSIONS.md` : Système de permissions
- `MODULE_MEDICAL.md` : Focus sur le module médical
- `DATABASE.md` : Schéma de la base

---

*Ces notes sont pour m'aider à comprendre rapidement l'app lors d'une nouvelle session.*

*Janvier 2025*
