# Fichier : core/models.py (VERSION STABLE COMPLÈTE - FIN ÉTAPE 4)

from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone

# ==============================================================================
# SECTION I : GESTION DES RESSOURCES HUMAINES (RH)
# ==============================================================================
# Cette section définit les entités principales liées aux agents, leurs centres
# d'affectation, leurs licences, formations et habilitations.
# ------------------------------------------------------------------------------

class Centre(models.Model):
    nom_centre = models.CharField(max_length=255, unique=True, help_text="Nom complet du centre (ex: DGA Essais en vol Istres)")
    code_centre = models.CharField(max_length=10, unique=True, help_text="Code mnémonique du centre (ex: IS, CA, TO)")
    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['code_centre']
    def __str__(self):
        return f"{self.nom_centre} ({self.code_centre})"

class Agent(models.Model):
    TYPE_AGENT_CHOICES = [("controleur", "Contrôleur"),("administratif", "Administratif"),("technique", "Technique"),("autre", "Autre")]
    id_agent = models.IntegerField(primary_key=True, help_text="ID legacy unique provenant des fichiers CSV")
    centre = models.ForeignKey('Centre', on_delete=models.SET_NULL, null=True, blank=True, related_name='agents', verbose_name="Centre de rattachement")
    reference = models.CharField(max_length=50, null=True, blank=True, help_text="Référence de l'agent (colonne 'Nom' dans agents.csv, ex: 'BO3')")
    trigram = models.CharField(max_length=10, unique=True, null=True, blank=True, help_text="Trigramme unique de l'agent")
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='agent_profile', verbose_name="Compte utilisateur associé")
    nom = models.CharField(max_length=100, blank=True, verbose_name="Nom de famille")
    prenom = models.CharField(max_length=100, blank=True, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True)
    nationalite = models.CharField(max_length=100, blank=True)
    actif = models.BooleanField(default=True, help_text="Indique si l'agent est actuellement en service actif")
    type_agent = models.CharField(max_length=50, choices=TYPE_AGENT_CHOICES, blank=True)
    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
        ordering = ['trigram', 'reference']
    def __str__(self):
        display_name = ""
        if self.nom and self.prenom:
            display_name = f"{self.prenom.capitalize()} {self.nom.upper()}"
        if self.trigram:
            return f"{display_name} ({self.trigram})" if display_name else self.trigram
        if self.reference:
            return f"{display_name} ({self.reference})" if display_name else self.reference
        return f"Agent ID {self.id_agent}"

class Licence(models.Model):
    STATUT_CHOICES = [("valide", "Valide"), ("suspendue", "Suspendue"), ("retiree", "Retirée"), ("expiree", "Expirée")]
    id_licence = models.IntegerField(unique=True, help_text="ID legacy de la licence provenant du CSV")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='licences', help_text="Agent détenteur de la licence")
    num_licence = models.CharField(max_length=50, blank=True)
    type_licence = models.CharField(max_length=100, blank=True)
    date_delivrance = models.DateField(null=True, blank=True)
    date_validite = models.DateField(null=True, blank=True, verbose_name="Date de fin de validité")
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default="valide")
    renouvellement = models.DateField(null=True, blank=True, help_text="Date du dernier renouvellement")
    suspension = models.DateField(null=True, blank=True, help_text="Date de début de la suspension")
    retrait = models.DateField(null=True, blank=True, help_text="Date du retrait définitif")
    class Meta:
        verbose_name = "Licence"
        verbose_name_plural = "Licences"
    def __str__(self):
        return f"Licence {self.num_licence or self.id_licence} de {self.agent}"

class Qualification(models.Model):
    STATUT_CHOICES = [("valide", "Valide"), ("en_cours", "En cours de validation"), ("expiree", "Expirée")]
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name='qualifications')
    type_qualif = models.CharField(max_length=100, verbose_name="Type de qualification")
    date_obtention = models.DateField()
    date_validite = models.DateField()
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default="valide")
    class Meta:
        verbose_name = "Qualification"
        verbose_name_plural = "Qualifications"
    def __str__(self):
        return f"{self.type_qualif} (Licence: {self.licence.num_licence or self.licence.id_licence})"

class Mention(models.Model):
    STATUT_CHOICES = [("valide", "Valide"), ("en_cours", "En cours"), ("expiree", "Expirée")]
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name='mentions')
    type_mention = models.CharField(max_length=100, verbose_name="Type de mention")
    date_obtention = models.DateField()
    date_validite = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default="valide")
    class Meta:
        verbose_name = "Mention"
        verbose_name_plural = "Mentions"
    def __str__(self):
        return f"Mention {self.type_mention} (Licence: {self.licence.num_licence or self.licence.id_licence})"

class CertificatMed(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='certificats_medicaux')
    date_visite = models.DateField()
    validite = models.DateField(help_text="Date de fin de validité du certificat")
    classe = models.CharField(max_length=50, help_text="Ex: Classe 1, Classe 2")
    restriction = models.TextField(blank=True)
    suspension = models.DateField(null=True, blank=True, help_text="Date de début de la suspension de l'aptitude")
    class Meta:
        verbose_name = "Certificat Médical"
        verbose_name_plural = "Certificats Médicaux"
        ordering = ['-validite']
    def __str__(self):
        return f"Certificat médical classe {self.classe} pour {self.agent} (valide jusqu'au {self.validite})"

class Module(models.Model):
    id_module = models.IntegerField(primary_key=True, help_text="ID legacy du module provenant du CSV")
    module_type = models.CharField(max_length=100, blank=True)
    module = models.CharField(max_length=255, blank=True)
    item = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=50, blank=True, db_column='numero', verbose_name="Numéro")
    sujet = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True, help_text="Date de la dernière mise à jour du contenu du module")
    validite = models.DateField(null=True, blank=True)
    support = models.CharField(max_length=50, blank=True)
    precisions = models.TextField(blank=True, verbose_name="Sujet / Précisions")
    class Meta:
        verbose_name = "Module de Formation (Catalogue)"
        verbose_name_plural = "Modules de Formation (Catalogue)"
    def __str__(self):
        return f"({self.id_module}) {self.module or self.module_type} - {self.sujet[:60] if self.sujet else 'N/A'}"

class Organisme(models.Model):
    nom_organisme = models.CharField(max_length=255, unique=True)
    type_organisme = models.CharField(max_length=100, blank=True, help_text="Ex: Interne, ENAC, Partenaire industriel")
    agrement = models.CharField(max_length=100, blank=True)
    class Meta:
        verbose_name = "Organisme de Formation"
        verbose_name_plural = "Organismes de Formation"
    def __str__(self):
        return self.nom_organisme

class Formation(models.Model):
    RESULTAT_CHOICES = [("reussi", "Réussi"), ("echoue", "Échoué"), ("en_cours", "En cours"), ("planifie", "Planifié")]
    id_formation = models.IntegerField(primary_key=True, help_text="ID legacy de la formation suivie provenant du CSV")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='formations', null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_formation')
    organisme = models.ForeignKey(Organisme, on_delete=models.SET_NULL, null=True, blank=True, related_name='formations_dispensees')
    date = models.DateField(null=True, blank=True, help_text="Date précise de la formation")
    annee = models.IntegerField(null=True, blank=True, help_text="Année de la formation, si la date n'est pas connue")
    duree = models.CharField(max_length=20, blank=True, help_text="Durée en jours, ou texte (ex: 'EPNER')")
    resultat = models.CharField(max_length=50, choices=RESULTAT_CHOICES, blank=True)
    class Meta:
        verbose_name = "Formation Suivie"
        verbose_name_plural = "Formations Suivies"
        ordering = ['-annee', '-date']
    def __str__(self):
        return f"Formation de {self.agent} en {self.annee or self.date}"

class Evaluation(models.Model):
    RESULTAT_CHOICES = [("satisfaisant", "Satisfaisant"), ("non_satisfaisant", "Non Satisfaisant"), ("en_cours", "En cours")]
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='evaluations')
    type_eval = models.CharField(max_length=100, verbose_name="Type d'évaluation")
    annee = models.IntegerField()
    date = models.DateField()
    resultat = models.CharField(max_length=50, choices=RESULTAT_CHOICES)
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
    def __str__(self):
        return f"Évaluation {self.type_eval} de {self.agent} le {self.date}"

class Habilitation(models.Model):
    STATUT_CHOICES = [("valide", "Valide"), ("expiree", "Expirée"), ("revoquee", "Révoquée")]
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='habilitations')
    type_hab = models.CharField(max_length=100, verbose_name="Type d'habilitation")
    date_obtention = models.DateField()
    date_expiration = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default="valide")
    class Meta:
        verbose_name = "Habilitation"
        verbose_name_plural = "Habilitations"
    def __str__(self):
        return f"Habilitation '{self.type_hab}' pour {self.agent}"

class Affectation(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='affectations')
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name='affectations_personnel')
    fonction = models.CharField(max_length=255)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True, help_text="Laisser vide si l'affectation est en cours")
    class Meta:
        verbose_name = "Affectation"
        verbose_name_plural = "Affectations"
    def __str__(self):
        return f"{self.agent} | {self.fonction} @ {self.centre.code_centre}"

# ==============================================================================
# SECTION II : GESTION DES VOLS
# ==============================================================================

class Client(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    contact = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom']
    def __str__(self):
        return self.nom

class Vol(models.Model):
    ETAT_CHOICES = [("en_attente", "En attente"), ("planifie", "Planifié"), ("en_cours", "En cours"), ("realise", "Réalisé"), ("annule", "Annulé")]
    TYPE_VOL_CHOICES = [("CAG", "CAG"), ("CAM", "CAM")]
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='vols')
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='vols')
    cca = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='vols_en_charge_cca', help_text="Agent en charge de la coordination du vol (CCA)")
    date_demande = models.DateField(auto_now_add=True)
    date_vol = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    etat = models.CharField(max_length=50, choices=ETAT_CHOICES, default="en_attente")
    type_vol = models.CharField(max_length=10, choices=TYPE_VOL_CHOICES)
    commentaire = models.TextField(blank=True)
    class Meta:
        verbose_name = "Vol"
        verbose_name_plural = "Vols"
        ordering = ['-date_vol', 'heure_debut']
    def __str__(self):
        return f"Vol {self.type_vol} pour {self.client} le {self.date_vol}"

class ControleVol(models.Model):
    vol = models.ForeignKey(Vol, on_delete=models.CASCADE, related_name='prises_en_charge')
    controleur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='vols_controles')
    heure_prise_en_charge = models.DateTimeField()
    heure_fin_prise_en_charge = models.DateTimeField()
    type_vol = models.CharField(max_length=10, choices=Vol.TYPE_VOL_CHOICES, help_text="Type de contrôle réellement effectué")
    class Meta:
        verbose_name = "Prise en charge de vol"
        verbose_name_plural = "Prises en charge de vols"
        ordering = ['heure_prise_en_charge']
    def __str__(self):
        return f"Contrôle de {self.vol} par {self.controleur}"

class AuditHeuresControle(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='audits_heures')
    periode = models.CharField(max_length=50, help_text="Format libre, ex: '2024-Q1', '2024-03'")
    heures_CAG = models.FloatField(default=0.0)
    heures_CAM = models.FloatField(default=0.0)
    date_audit = models.DateField(auto_now_add=True)
    class Meta:
        verbose_name = "Audit d'heures de contrôle"
        verbose_name_plural = "Audits d'heures de contrôle"
        unique_together = ('agent', 'periode')
    def __str__(self):
        return f"Audit heures de {self.agent} pour la période {self.periode}"

# ==============================================================================
# SECTION III : PARAMETRAGE DYNAMIQUE ET GESTION DES ROLES
# ==============================================================================

class Parametre(models.Model):
    TYPE_VALEUR_CHOICES = [('string', 'Texte'), ('integer', 'Entier'), ('boolean', 'Booléen'), ('date', 'Date')]
    nom = models.CharField(max_length=100, unique=True, help_text="Nom technique du paramètre")
    description = models.TextField()
    valeur_defaut = models.CharField(max_length=255)
    type_valeur = models.CharField(max_length=50, choices=TYPE_VALEUR_CHOICES)
    class Meta:
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"
    def __str__(self):
        return self.nom

class ValeurParametre(models.Model):
    parametre = models.ForeignKey(Parametre, on_delete=models.CASCADE, related_name='valeurs')
    valeur = models.CharField(max_length=255)
    centre = models.ForeignKey('Centre', on_delete=models.CASCADE, null=True, blank=True, help_text="Si ce paramètre est spécifique à un centre")
    responsable = models.ForeignKey('Agent', on_delete=models.PROTECT, help_text="Agent responsable de cette valeur")
    est_global = models.BooleanField(default=False, help_text="Cochez si la valeur s'applique à tous les centres")
    class Meta:
        verbose_name = "Valeur de Paramètre"
        verbose_name_plural = "Valeurs de Paramètres"
        unique_together = ('parametre', 'centre')
    def __str__(self):
        scope = f"pour {self.centre.code_centre}" if self.centre else "global"
        return f"{self.parametre.nom} ({scope}) = {self.valeur}"

class Role(models.Model):
    class RoleScope(models.TextChoices):
        CENTRAL = 'CENTRAL', 'Central'
        LOCAL = 'LOCAL', 'Local'
        OPERATIONNEL = 'OPERATIONNEL', 'Opérationnel'
    class RoleLevel(models.TextChoices):
        ENCADREMENT = 'ENCADREMENT', 'Encadrement'
        MANAGEMENT = 'MANAGEMENT', 'Management'
        EXECUTION = 'EXECUTION', 'Exécution'
    nom = models.CharField(max_length=100, unique=True)
    groups = models.ManyToManyField(Group, blank=True, verbose_name="Groupes de permissions associés", help_text="Les ensembles de permissions techniques que ce rôle confère.")
    scope = models.CharField(max_length=20, choices=RoleScope.choices, verbose_name="Portée du rôle", default=RoleScope.OPERATIONNEL)
    level = models.CharField(max_length=20, choices=RoleLevel.choices, verbose_name="Niveau hiérarchique", default=RoleLevel.EXECUTION)
    class Meta:
        verbose_name = "Rôle / Fonction Métier"
        verbose_name_plural = "Rôles / Fonctions Métier"
        ordering = ['scope', 'level', 'nom']
    def __str__(self):
        return self.nom

class AgentRole(models.Model):
    agent = models.ForeignKey('Agent', on_delete=models.CASCADE, related_name='roles_assignes')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='agents_assignes')
    centre = models.ForeignKey('Centre', on_delete=models.CASCADE, null=True, blank=True, help_text="Obligatoire si le rôle est local ou opérationnel.")
    date_debut = models.DateField(default=timezone.now, verbose_name="Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin", help_text="Laisser vide si l'attribution est à durée indéterminée.")
    class Meta:
        verbose_name = "Attribution de Rôle"
        verbose_name_plural = "Attributions de Rôles"
        unique_together = ('agent', 'role', 'centre', 'date_debut')
    def __str__(self):
        scope = f" @ {self.centre.code_centre}" if self.centre else " (Global)"
        return f"{self.agent} a le rôle '{self.role}'{scope}"
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.agent.user and (self.date_fin is None or self.date_fin >= timezone.now().date()):
            for group in self.role.groups.all():
                self.agent.user.groups.add(group)
    def delete(self, *args, **kwargs):
        user = self.agent.user
        role_to_remove = self.role
        super().delete(*args, **kwargs)
        if user and role_to_remove:
            active_roles = AgentRole.objects.filter(agent=self.agent, date_fin__isnull=True).exclude(pk=self.pk)
            for group in role_to_remove.groups.all():
                if not active_roles.filter(role__groups=group).exists():
                    user.groups.remove(group)
    
    # Dans core/models.py, à la fin de la SECTION III

class Delegation(models.Model):
    """Trace la délégation temporaire des droits d'un agent à un autre."""
    delegant = models.ForeignKey(
        'Agent', 
        on_delete=models.CASCADE, 
        related_name='delegations_donnees',
        help_text="L'agent qui donne ses droits."
    )
    delegataire = models.ForeignKey(
        'Agent', 
        on_delete=models.CASCADE, 
        related_name='delegations_recues',
        help_text="L'agent qui reçoit les droits (l'intérimaire)."
    )
    date_debut = models.DateField(help_text="Début de la période de délégation.")
    date_fin = models.DateField(help_text="Fin de la période de délégation.")
    motivee_par = models.CharField(max_length=255, blank=True, help_text="Raison de la délégation (ex: Congés, Déplacement).")
    creee_par = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='delegations_creees',
        help_text="Utilisateur qui a enregistré cette délégation."
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Délégation de droits"
        verbose_name_plural = "Délégations de droits"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.delegant} délègue à {self.delegataire} du {self.date_debut} au {self.date_fin}"

# ==============================================================================
# SECTION IV : GESTION DOCUMENTAIRE
# ==============================================================================

class DocumentType(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = "Type de Document"
        verbose_name_plural = "Types de Documents"
    def __str__(self):
        return self.nom

class Document(models.Model):
    type_document = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    fichier = models.FileField(upload_to='documents/current/%Y/%m/', blank=True, help_text="Fichier de la version actuellement en vigueur")
    reference = models.CharField(max_length=100, unique=True)
    date_creation = models.DateField(auto_now_add=True)
    date_mise_a_jour = models.DateField(auto_now=True)
    est_archive = models.BooleanField(default=False)
    responsable_sms = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_sous_responsabilite')
    centres_visibles = models.ManyToManyField(Centre, blank=True, related_name='documentation_visible', help_text="Centres pour qui ce document est applicable")
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
    def __str__(self):
        return f"{self.reference} - {self.titre}"

class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    numero_version = models.CharField(max_length=20)
    fichier = models.FileField(upload_to='documents/archives/%Y/%m/')
    date_version = models.DateField()
    commentaire = models.TextField(blank=True, help_text="Résumé des modifications apportées dans cette version")
    class Meta:
        verbose_name = "Version de Document"
        verbose_name_plural = "Versions de Documents"
        ordering = ['-date_version']
        unique_together = ('document', 'numero_version')
    def __str__(self):
        return f"{self.document.reference} - v{self.numero_version}"

class SignatureCircuit(models.Model):
    STATUT_CHOICES = [('en_attente', 'En attente'), ('signe', 'Signé'), ('refuse', 'Refusé')]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='circuit_signatures')
    ordre = models.PositiveIntegerField(help_text="Ordre de l'étape dans le circuit (1, 2, 3...)")
    organisme = models.CharField(max_length=255, help_text="Entité ou fonction qui doit signer (ex: Chef de centre, Responsable QS)")
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, help_text="Agent qui a effectivement signé")
    date_signature = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='en_attente')
    commentaire = models.TextField(blank=True)
    class Meta:
        verbose_name = "Étape de Signature"
        verbose_name_plural = "Étapes de Signature"
        ordering = ['document', 'ordre']
        unique_together = ('document', 'ordre')
    def __str__(self):
        return f"Étape {self.ordre} pour {self.document.reference}"

# ==============================================================================
# SECTION V : GESTION DU CHANGEMENT ET MRR (MANAGEMENT OF REGULATORY REQUIREMENTS)
# ==============================================================================

class CentreRole(models.Model):
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    class Meta:
        verbose_name = "Rôle au sein du Centre"
        verbose_name_plural = "Rôles au sein des Centres"
    def __str__(self):
        return f"{self.agent} est {self.role} à {self.centre.code_centre}"

class ResponsableSMS(models.Model):
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='responsabilite_sms')
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    class Meta:
        verbose_name = "Responsable SMS"
        verbose_name_plural = "Responsables SMS"
    def __str__(self):
        return f"Responsabilité SMS de {self.agent}"

class MRR(models.Model):
    STATUT_CHOICES = [('ouvert', 'Ouvert'), ('en_cours', 'En cours'), ('clos', 'Clos'), ('annule', 'Annulé')]
    intitule = models.CharField(max_length=255)
    date_ouverture = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='ouvert')
    commentaires = models.TextField(blank=True)
    archive = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Fiche MRR"
        verbose_name_plural = "Fiches MRR"
    def __str__(self):
        return self.intitule

class MRRSignataire(models.Model):
    mrr = models.ForeignKey(MRR, on_delete=models.CASCADE, related_name='signataires')
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT)
    date_signature = models.DateField(null=True, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = ('mrr', 'agent')
        verbose_name = "Signataire MRR"
        verbose_name_plural = "Signataires MRR"
        
class MRRProgression(models.Model):
    mrr = models.ForeignKey(MRR, on_delete=models.CASCADE, related_name='progression')
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=100)
    commentaire = models.TextField()
    class Meta:
        verbose_name = "Progression MRR"
        verbose_name_plural = "Progressions MRR"
        ordering = ['-date']

class Changement(models.Model):
    STATUT_CHOICES = [('identifie', 'Identifié'), ('analyse', 'En analyse'), ('approuve', 'Approuvé'), ('implemente', 'Implémenté')]
    mrr = models.ForeignKey(MRR, on_delete=models.SET_NULL, null=True, blank=True, related_name='changements')
    origine = models.TextField(help_text="Qui ou quoi est à l'origine du changement")
    description = models.TextField()
    date_creation = models.DateField(auto_now_add=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='identifie')
    responsable_sms = models.ForeignKey(ResponsableSMS, on_delete=models.PROTECT)
    impact = models.TextField(help_text="Analyse d'impact du changement")
    archive = models.BooleanField(default=False)
    class Meta:
        verbose_name = "Demande de Changement"
        verbose_name_plural = "Demandes de Changement"
    def __str__(self):
        return f"Changement: {self.description[:80]}"

class Action(models.Model):
    STATUT_CHOICES = [('a_faire', 'À faire'), ('en_cours', 'En cours'), ('fait', 'Fait'), ('annule', 'Annulé')]
    changement = models.ForeignKey(Changement, on_delete=models.CASCADE, related_name='actions')
    numero_action = models.CharField(max_length=50, blank=True)
    type_action = models.CharField(max_length=100, blank=True, help_text="Ex: Documentaire, Formation, Technique")
    description = models.TextField()
    date_prevue = models.DateField()
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_faire')
    archive = models.BooleanField(default=False)
    class Meta:
        verbose_name = "Action de Changement"
        verbose_name_plural = "Actions de Changement"
    def __str__(self):
        return self.description[:80]

class Notification(models.Model):
    STATUT_CHOICES = [('a_envoyer', 'À envoyer'), ('envoye', 'Envoyé'), ('erreur', 'Erreur')]
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='notifications')
    destinataire = models.CharField(max_length=255, help_text="Email ou nom de l'agent/groupe")
    date_envoi = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_envoyer')
    message = models.TextField()
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

# ==============================================================================
# SECTION VI : QUALITE/SECURITE DES VOLS (QS/SMS)
# ==============================================================================

class ResponsableQSCentral(models.Model):
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='responsabilite_qs_central')
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    class Meta:
        verbose_name = "Responsable QS Central"
        verbose_name_plural = "Responsables QS Central"
    def __str__(self):
        return f"Responsabilité QS Centrale de {self.agent}"

class EvenementQS(models.Model):
    STATUT_CHOICES = [('ouvert', 'Ouvert'), ('analyse', 'En analyse'), ('clos', 'Clos')]
    date_evenement = models.DateField()
    type_evenement = models.CharField(max_length=100)
    description = models.TextField()
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT)
    rapporteur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='evenements_rapportes_qs')
    niveau_gravite = models.CharField(max_length=50, help_text="Ex: Mineur, Significatif, Majeur")
    analyse = models.TextField(blank=True, help_text="Analyse à froid de l'événement")
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='ouvert')
    class Meta:
        verbose_name = "Événement QS"
        verbose_name_plural = "Événements QS"
    def __str__(self):
        return f"Événement du {self.date_evenement}: {self.type_evenement}"

class RecommendationQS(models.Model):
    STATUT_CHOICES = [('proposee', 'Proposée'), ('acceptee', 'Acceptée'), ('refusee', 'Refusée'), ('implementee', 'Implémentée')]
    evenement = models.ForeignKey(EvenementQS, on_delete=models.CASCADE, related_name='recommandations')
    description = models.TextField()
    priorite = models.CharField(max_length=50, help_text="Ex: Haute, Moyenne, Basse")
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='proposee')
    date_emission = models.DateField(auto_now_add=True)
    date_echeance = models.DateField()
    responsable = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='recommandations_qs_responsable')
    diffusion_nationale = models.BooleanField(default=False)
    centres_cibles = models.ManyToManyField(Centre, blank=True, related_name='recommandations_qs_cibles')
    class Meta:
        verbose_name = "Recommandation QS"
        verbose_name_plural = "Recommandations QS"
    def __str__(self):
        return f"Reco: {self.description[:80]}"

class ActionQS(models.Model):
    STATUT_CHOICES = [('a_faire', 'À faire'), ('en_cours', 'En cours'), ('fait', 'Fait'), ('annule', 'Annulé')]
    recommendation = models.ForeignKey(RecommendationQS, on_delete=models.CASCADE, related_name='actions_qs')
    description = models.TextField()
    date_prevue = models.DateField()
    date_realisation = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_faire')
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, help_text="Lien vers une formation si l'action en est une")
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, help_text="Lien vers un document si l'action est documentaire")
    archive = models.BooleanField(default=False)
    class Meta:
        verbose_name = "Action QS"
        verbose_name_plural = "Actions QS"
    def __str__(self):
        return f"Action QS: {self.description[:80]}"

class AuditQS(models.Model):
    auditeur = models.ForeignKey(Agent, on_delete=models.PROTECT)
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='audits_recus')
    date_audit = models.DateField()
    type_audit = models.CharField(max_length=100)
    rapport = models.TextField(blank=True, help_text="Résumé du rapport d'audit")
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, help_text="Lien vers le rapport d'audit complet")
    class Meta:
        verbose_name = "Audit QS"
        verbose_name_plural = "Audits QS"

class EvaluationRisqueQS(models.Model):
    STATUT_CHOICES = [('identifie', 'Identifié'), ('evalue', 'Évalué'), ('maitrise', 'Maîtrisé'), ('clos', 'Clos')]
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT)
    date_evaluation = models.DateField()
    description = models.TextField()
    niveau_risque = models.CharField(max_length=50, help_text="Ex: Acceptable, Tolérable, Inacceptable")
    recommandations = models.TextField(blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='identifie')
    class Meta:
        verbose_name = "Évaluation de Risque QS"
        verbose_name_plural = "Évaluations de Risques QS"

class NotificationQS(models.Model):
    STATUT_CHOICES = [('a_envoyer', 'À envoyer'), ('envoye', 'Envoyé'), ('erreur', 'Erreur')]
    action = models.ForeignKey(ActionQS, on_delete=models.CASCADE, related_name='notifications_qs')
    destinataire = models.CharField(max_length=255)
    date_envoi = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_envoyer')
    message = models.TextField()
    class Meta:
        verbose_name = "Notification QS"
        verbose_name_plural = "Notifications QS"

# ==============================================================================
# SECTION VII : GESTION DU TOUR DE SERVICE
# ==============================================================================

class PositionJour(models.Model):
    """
    Définit le catalogue des positions/postes assignables dans le planning.
    Chaque centre gère sa propre liste de positions.
    """
    class Categorie(models.TextChoices):
        TRAVAIL_SITE = 'SITE', 'Travail sur site'
        TRAVAIL_HORS_SITE = 'HORS_SITE', 'Travail hors site'
        NON_TRAVAIL = 'NON_TRAVAIL', 'Non travail'

    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name='positions_jour', 
        verbose_name="Centre associé"
    )
    nom = models.CharField(
        max_length=20, 
        help_text="Nom court et unique de la position (ex: 'J1', 'Q2', 'RTT', 'MIS')"
    )
    description = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Description complète (ex: 'Journée normale', 'Mission extérieure')"
    )
    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        verbose_name="Catégorie",
        help_text="Classification de la position pour les statistiques et règles."
    )

    class Meta:
        verbose_name = "Position Jour (Planning)"
        verbose_name_plural = "Positions Jour (Planning)"
        unique_together = ('centre', 'nom') # Assure que 'J1' est unique pour un centre donné
        ordering = ['centre', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.centre.code_centre})"

class TourDeService(models.Model):
    """Représente l'affectation d'un agent pour une journée spécifique."""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='tours_de_service')
    date = models.DateField(db_index=True)
    position_matin = models.ForeignKey(
        PositionJour, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='affectations_matin'
    )
    position_apres_midi = models.ForeignKey(
        PositionJour, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='affectations_apres_midi'
    )
    commentaire = models.TextField(blank=True, null=True)
    modifie_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    class Meta:
        verbose_name = "Tour de Service"
        verbose_name_plural = "Tours de Service"
        unique_together = ('agent', 'date')
        ordering = ['-date', 'agent']

    def __str__(self):
        return f"Tour de {self.agent} le {self.date}"

class TourDeServiceHistorique(models.Model):
    """Trace complète des modifications apportées à un tour de service."""
    class TypeModification(models.TextChoices):
        CREATION = 'CREATION', 'Création'
        MODIFICATION = 'MODIFICATION', 'Modification'

    tour_de_service_original = models.ForeignKey(TourDeService, on_delete=models.SET_NULL, null=True, related_name='historique')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, related_name='+')
    date = models.DateField()
    position_matin = models.ForeignKey(PositionJour, on_delete=models.SET_NULL, null=True, related_name='+')
    position_apres_midi = models.ForeignKey(PositionJour, on_delete=models.SET_NULL, null=True, related_name='+')
    commentaire = models.TextField(blank=True, null=True)
    modifie_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='historique_tours_modifies')
    modifie_le = models.DateTimeField()
    type_modification = models.CharField(max_length=20, choices=TypeModification.choices)

    class Meta:
        verbose_name = "Historique de Tour de Service"
        verbose_name_plural = "Historiques des Tours de Service"
        ordering = ['-modifie_le']

    def __str__(self):
        return f"Historique pour {self.agent} le {self.date} ({self.modifie_le.strftime('%d/%m/%Y %H:%M')})"