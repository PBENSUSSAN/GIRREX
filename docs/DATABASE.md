# 🗄️ SCHÉMA DE BASE DE DONNÉES GIRREX

## 🎯 Ce que je dois savoir

Ce fichier décrit les tables principales et leurs relations. Pour comprendre rapidement la BDD sans faire de requêtes.

---

## 📊 TABLES PRINCIPALES PAR MODULE

### 🏛️ CORE - RH & Médical

#### Agent (core_agent)
```sql
id_agent          PK
trigram           UNIQUE (3 lettres)
nom, prenom
email
centre_id         FK → Centre
user_id           FK → User (OneToOne)
actif             BOOLEAN
date_entree
date_sortie
```
**Relations** :
- `user` → User Django (OneToOne)
- `centre` → Centre
- `certificats_medicaux` → CertificatMed (OneToMany)
- `rendez_vous_medicaux` → RendezVousMedical (OneToMany)
- `roles_assignes` → AgentRole (OneToMany)

#### Centre (core_centre)
```sql
id                PK
code_centre       UNIQUE (ex: AIX, MRS)
nom_centre
type_centre       (ACC, APP)
adresse
capacite_max
actif
```

#### CertificatMed (core_certificatmed)
```sql
id                        PK
agent_id                  FK → Agent
date_visite               DATE
resultat                  VARCHAR (APTE, INAPTE, INAPTE_TEMP)
date_expiration_aptitude  DATE (obligatoire si APTE)
restrictions              TEXT
organisme_medical
fichier_certificat        FILE (optionnel)
saisi_par_id              FK → User
date_saisie               DATETIME
```
**INDEX** : `agent_id`, `date_visite`, `resultat`

#### RendezVousMedical (core_rendezvousmedical)
```sql
id                    PK
agent_id              FK → Agent
date_heure_rdv        DATETIME
organisme_medical
statut                VARCHAR (PLANIFIE, REPORTE, REALISE, ANNULE)
certificat_genere_id  FK → CertificatMed (nullable)
created_by_id         FK → User
modified_by_id        FK → User
date_creation         DATETIME
date_modification     DATETIME
```

#### HistoriqueRDV (core_historiquerdv)
```sql
id                PK
rdv_id            FK → RendezVousMedical
action            VARCHAR (CREATION, MODIFICATION, ANNULATION, REALISATION)
utilisateur_id    FK → User
date_action       DATETIME
ancien_statut
nouveau_statut
ancienne_date
nouvelle_date
commentaire       TEXT
```

#### ArretMaladie (core_arretmaladie)
```sql
id                PK
agent_id          FK → Agent
date_debut        DATE
date_fin          DATE
fichier_justif    FILE
commentaire       TEXT
```
**Property** : `est_long_terme` (> 21 jours)

---

### 🔐 CORE - Paramétrage & Rôles

#### Role (core_role)
```sql
id          PK
nom         VARCHAR UNIQUE (CHEF_DE_CENTRE, FORM_LOCAL, etc.)
scope       VARCHAR (CENTRAL, LOCAL, OPERATIONNEL)
level       VARCHAR (ENCADREMENT, MANAGEMENT, EXECUTION)
groups      M2M → Group Django
```
**⚠️ NE JAMAIS MODIFIER CETTE TABLE**

#### AgentRole (core_agentrole)
```sql
id           PK
agent_id     FK → Agent
role_id      FK → Role
centre_id    FK → Centre (nullable, obligatoire si LOCAL/OPERATIONNEL)
date_debut   DATE
date_fin     DATE (nullable)
```
**UNIQUE** : (agent, role, centre, date_debut)

#### Delegation (core_delegation)
```sql
id                    PK
agent_role_delegue_id FK → AgentRole
delegant_id           FK → Agent
delegataire_id        FK → Agent
date_debut            DATE
date_fin              DATE
motivee_par           VARCHAR
creee_par_id          FK → User
date_creation         DATETIME
```

---

### 🎓 COMPETENCES

#### Brevet (competences_brevet)
```sql
id              PK
agent_id        FK → Agent
numero_brevet   VARCHAR UNIQUE
type_brevet     VARCHAR
date_obtention  DATE
date_expiration DATE
actif           BOOLEAN
```

#### Qualification (competences_qualification)
```sql
id          PK
brevet_id   FK → Brevet
centre_id   FK → Centre
flux        VARCHAR (CAM, CAG)
date_debut  DATE
date_fin    DATE (nullable)
statut      VARCHAR (ACTIVE, SUSPENDUE, EXPIREE)
```

#### MentionUniteAnnuelle (competences_mentionuniteannuelle)
```sql
id                          PK
qualification_id            FK → Qualification
type_flux                   VARCHAR (CAM, CAG)
date_debut_cycle            DATE
date_fin_cycle              DATE
statut                      VARCHAR (ACTIF, SUSPENDU_*, EN_ATTENTE, ARCHIVE)
annee_cycle                 INT (1, 2, 3 pour cycle triennal)
date_derniere_activite      DATE

# Compteurs d'heures
heures_cam_effectuees       FLOAT
heures_cag_acs_effectuees   FLOAT
heures_cag_aps_effectuees   FLOAT
heures_tour_effectuees      FLOAT
heures_en_cdq               FLOAT
heures_en_supervision       FLOAT
heures_en_isp               FLOAT
```
**⚠️ IMPORTANT** : Les compteurs sont mis à jour par agrégation des SaisieActivite

#### MentionLinguistique (competences_mentionlinguistique)
```sql
id              PK
brevet_id       FK → Brevet
langue          VARCHAR (ANGLAIS)
niveau          VARCHAR (4, 5, 6)
date_obtention  DATE
date_echeance   DATE
```

#### SuiviFormationReglementaire (competences_suiviformationreglementaire)
```sql
id                  PK
brevet_id           FK → Brevet
formation_id        FK → FormationReglementaire
date_realisation    DATE
date_echeance       DATE
certificat          FILE
```
**Formation importante** : `fh-raf-aero` (RAF AERO, tous les 3 ans)

#### RegleDeRenouvellement (competences_reglerenouvellement)
```sql
id                          PK
centres                     M2M → Centre
seuil_heures_total          INT
seuil_heures_cam            INT
seuil_heures_cag_acs        INT
seuil_heures_cag_aps        INT
seuil_heures_tour           INT
```

---

### ✈️ ACTIVITES

#### Vol (activites_vol)
```sql
id                PK
date_vol          DATE
heure_debut       TIME
heure_fin         TIME
duree_reelle      FLOAT (calculée en heures)
flux              VARCHAR (CAM, CAG_ACS, CAG_APS, TOUR)
centre_id         FK → Centre
indicatif         VARCHAR
type_appareil
```
**INDEX** : `date_vol`, `centre_id`, `flux`

#### SaisieActivite (activites_saisieactivite)
```sql
id          PK
vol_id      FK → Vol
agent_id    FK → Agent
role        VARCHAR (controleur, cdq, superviseur, isp, stagiaire)
```
**UNIQUE** : (vol, agent, role)

**⚠️ Ces activités alimentent les compteurs MUA**

---

### 🛡️ QS - Qualité & Sécurité

#### FNE (qs_fne)
```sql
id                      PK
numero_fne              VARCHAR UNIQUE
date_evenement          DATE
centre_id               FK → Centre
declarant_id            FK → Agent
type_evenement
gravite
statut                  VARCHAR (DECLAREE, PRE_CLASSIFIEE, CLASSIFIEE, CLOTUREE)
classification_finale
date_cloture
```

---

### 🔒 CYBER - SMSI

#### Risque (cyber_risque)
```sql
id              PK
reference       VARCHAR
libelle
centre_id       FK → Centre (nullable si national)
niveau_risque   VARCHAR (FAIBLE, MOYEN, ELEVE, CRITIQUE)
statut          VARCHAR (OUVERT, EN_TRAITEMENT, MITIGE, ACCEPTE)
```

---

### 🔧 TECHNIQUE

#### Panne (technique_panne)
```sql
id                  PK
date_debut          DATETIME
equipement
centre_id           FK → Centre
description         TEXT
declarant_id        FK → Agent
statut              VARCHAR (OUVERTE, EN_COURS, RESOLUE)
date_resolution     DATETIME
```

#### MISO (technique_miso)
```sql
id                  PK
date_miso           DATETIME
type_miso           VARCHAR (MISE_EN_SERVICE, HORS_SERVICE)
equipement
centre_id           FK → Centre
decideur_id         FK → Agent
motif               TEXT
```

---

## 🔗 RELATIONS CRITIQUES

### Socle de validité MUA

```
Agent
  ├─→ CertificatMed (le plus récent APTE valide)
  ├─→ MentionLinguistique (ANGLAIS valide)
  └─→ SuiviFormationReglementaire (RAF AERO valide)
        ↓
    Si TOUS valides → Socle MUA valide
```

### Chaîne des compétences

```
Agent
  └─→ Brevet
        └─→ Qualification (par centre)
              └─→ MentionUniteAnnuelle (MUA)
                    ↑
                    └─ SaisieActivite (agrégation heures)
```

### Workflow médical

```
Agent
  ├─→ RendezVousMedical (PLANIFIE)
  │     └─→ HistoriqueRDV (traçabilité)
  │           ↓
  │       Saisie résultat
  │           ↓
  └─→ CertificatMed (APTE)
        ↓
    Impact sur Socle MUA
```

---

## 📊 REQUÊTES UTILES

### Trouver le certificat médical actif d'un agent

```sql
SELECT * FROM core_certificatmed
WHERE agent_id = ?
  AND resultat = 'APTE'
  AND date_expiration_aptitude >= CURRENT_DATE
ORDER BY date_visite DESC
LIMIT 1;
```

### Trouver les MUA actives d'un agent

```sql
SELECT mua.*
FROM competences_mentionuniteannuelle mua
JOIN competences_qualification q ON mua.qualification_id = q.id
JOIN competences_brevet b ON q.brevet_id = b.id
WHERE b.agent_id = ?
  AND mua.statut = 'ACTIF'
  AND mua.date_debut_cycle <= CURRENT_DATE
  AND mua.date_fin_cycle >= CURRENT_DATE;
```

### Trouver les agents d'un centre avec certificat expirant dans 30 jours

```sql
SELECT a.trigram, c.date_expiration_aptitude
FROM core_agent a
JOIN core_certificatmed c ON c.agent_id = a.id_agent
WHERE a.centre_id = ?
  AND a.actif = true
  AND c.resultat = 'APTE'
  AND c.date_expiration_aptitude BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
  AND c.id = (
    SELECT MAX(id) FROM core_certificatmed
    WHERE agent_id = a.id_agent
  );
```

### Calculer les heures d'un agent sur une période

```sql
SELECT 
  v.flux,
  sa.role,
  SUM(v.duree_reelle) as total_heures
FROM activites_saisieactivite sa
JOIN activites_vol v ON sa.vol_id = v.id
WHERE sa.agent_id = ?
  AND v.date_vol BETWEEN ? AND ?
GROUP BY v.flux, sa.role;
```

---

## 🔍 INDEX IMPORTANTS

### Créés automatiquement par Django

```sql
-- Clés étrangères (index auto)
core_agent.centre_id
core_agent.user_id
core_certificatmed.agent_id
competences_mua.qualification_id
activites_saisieactivite.agent_id
activites_saisieactivite.vol_id
```

### À considérer si performance

```sql
CREATE INDEX idx_cert_actif ON core_certificatmed(agent_id, resultat, date_expiration_aptitude);
CREATE INDEX idx_vol_date ON activites_vol(date_vol, centre_id);
CREATE INDEX idx_mua_statut ON competences_mentionuniteannuelle(statut, date_fin_cycle);
```

---

## ⚠️ POINTS D'ATTENTION

### Soft Delete vs Hard Delete

- **Agent** : `actif = False` (soft delete)
- **RendezVousMedical** : `statut = ANNULE` (soft delete)
- **MUA** : `statut = ARCHIVE` (soft delete)

Ne JAMAIS supprimer physiquement pour conserver l'historique.

### Contraintes d'intégrité

- **AgentRole** : UNIQUE(agent, role, centre, date_debut)
- **SaisieActivite** : UNIQUE(vol, agent, role)
- **Agent.trigram** : UNIQUE
- **Centre.code_centre** : UNIQUE

### Cascade

```python
# Définir on_delete correctement
agent = ForeignKey(Agent, on_delete=models.CASCADE)     # Supprime les enfants
agent = ForeignKey(Agent, on_delete=models.PROTECT)     # Empêche suppression
agent = ForeignKey(Agent, on_delete=models.SET_NULL)    # Met à NULL
```

---

## 🧪 MIGRATIONS

### Créer une migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### Créer une migration vide (pour script SQL)

```bash
python manage.py makemigrations --empty mon_app
```

### Revenir en arrière

```bash
python manage.py migrate mon_app 0003  # Revenir à la migration 0003
```

---

## 📚 VOIR AUSSI

- `ARCHITECTURE.md` : Structure générale
- `MODULES.md` : Description des modules
- `MODULE_MEDICAL.md` : Focus médical
- `CONVENTIONS.md` : Conventions de nommage

---

*Ce schéma représente l'état actuel de la BDD. Consulter les models Django pour les détails.*

*Janvier 2025*
