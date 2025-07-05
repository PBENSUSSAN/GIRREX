# core/models.py

from django.db import models
from django.contrib.auth.models import User

# ==============================================================================
# SECTION I : GESTION DES RESSOURCES HUMAINES (RH)
# ==============================================================================
# Cette section définit les entités principales liées aux agents, leurs centres
# d'affectation, leurs licences, formations et habilitations.
# ------------------------------------------------------------------------------

class Centre(models.Model):
    """
    Représente un centre de contrôle ou une entité administrative.
    Exemples : Istres, Cazaux, Toulouse...
    """
    # L'ID est géré automatiquement par Django.
    nom_centre = models.CharField(max_length=255, unique=True, help_text="Nom complet du centre (ex: DGA Essais en vol Istres)")
    code_centre = models.CharField(max_length=10, unique=True, help_text="Code mnémonique du centre (ex: IS, CA, TO)")

    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['code_centre']

    def __str__(self):
        return f"{self.nom_centre} ({self.code_centre})"

class Agent(models.Model):
    """
    Représente un employé, qu'il soit contrôleur, administratif, etc.
    L'ID primaire est forcé pour correspondre au 'id_agent' des fichiers CSV,
    simplifiant grandement l'importation et les relations initiales.
    """
    TYPE_AGENT_CHOICES = [
        ("controleur", "Contrôleur"),
        ("administratif", "Administratif"),
        ("technique", "Technique"),
        ("autre", "Autre"),
    ]
    
    # --- Champs existants ---
    id_agent = models.IntegerField(primary_key=True, help_text="ID legacy unique provenant des fichiers CSV")
    centre = models.ForeignKey('Centre', on_delete=models.SET_NULL, null=True, blank=True, related_name='agents', verbose_name="Centre de rattachement")
    
    # Données issues du CSV agents.csv
    reference = models.CharField(max_length=50, null=True, blank=True, help_text="Référence de l'agent (colonne 'Nom' dans agents.csv, ex: 'BO3')")
    trigram = models.CharField(max_length=10, unique=True, null=True, blank=True, help_text="Trigramme unique de l'agent")

    # --- CHAMP AJOUTÉ POUR LE LIEN AVEC L'UTILISATEUR DJANGO ---
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='agent_profile',
        verbose_name="Compte utilisateur associé"
    )

    # --- Champs à compléter ultérieurement (gardés pour la structure) ---
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
        # Amélioration de la méthode __str__ pour utiliser les nouvelles infos
        display_name = ""
        if self.nom and self.prenom:
            display_name = f"{self.prenom.capitalize()} {self.nom.upper()}"
        
        if self.trigram:
            return f"{display_name} ({self.trigram})" if display_name else self.trigram
        
        if self.reference:
            return f"{display_name} ({self.reference})" if display_name else self.reference

        return f"Agent ID {self.id_agent}"

class Licence(models.Model):
    """
    Détient les informations sur la licence de contrôle d'un agent.
    """
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
    """
    Qualification spécifique associée à une licence (ex: Approche, Tour).
    """
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
    """
    Mention additionnelle sur une licence (ex: Mention linguistique).
    """
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
    """
    Certificat d'aptitude médicale d'un agent.
    """
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
    """
    Un module de formation (théorique ou pratique) défini dans le programme.
    C'est le "catalogue" des formations possibles.
    """
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
    """
    Organisme de formation, interne ou externe.
    """
    nom_organisme = models.CharField(max_length=255, unique=True)
    type_organisme = models.CharField(max_length=100, blank=True, help_text="Ex: Interne, ENAC, Partenaire industriel")
    agrement = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Organisme de Formation"
        verbose_name_plural = "Organismes de Formation"

    def __str__(self):
        return self.nom_organisme

class Formation(models.Model):
    """
    Trace une session de formation spécifique suivie par un agent.
    C'est une "instance" d'un Module pour un Agent donné.
    """
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
    """
    Évaluation périodique (technique, pratique) d'un agent.
    """
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
    """
    Habilitation spécifique non liée à une licence (ex: secret défense, accès salle).
    """
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
    """
    Détaille l'affectation d'un agent à une fonction dans un centre donné.
    Permet de tracer l'historique des postes.
    """
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
# Modèles pour la planification, le suivi et l'audit des vols d'essais.
# ------------------------------------------------------------------------------

class Client(models.Model):
    """
    Représente un client (industriel, DGA, etc.) demandeur d'un vol.
    """
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
    """
    Planification d'un vol, de la demande à la réalisation.
    """
    ETAT_CHOICES = [("en_attente", "En attente"), ("planifie", "Planifié"), ("en_cours", "En cours"), ("realise", "Réalisé"), ("annule", "Annulé")]
    TYPE_VOL_CHOICES = [("CAG", "CAG"), ("CAM", "CAM")]
    
    # on_delete=PROTECT pour éviter de supprimer un client/centre/agent s'il a des vols associés.
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
    """
    Trace la prise en charge d'un vol par un contrôleur.
    Un vol peut être transféré entre plusieurs contrôleurs.
    """
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
    """
    Résultat d'un audit des heures de contrôle (CAG/CAM) pour un agent
    sur une période donnée, pour le maintien de compétence.
    """
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
# Modèles pour la configuration de l'application et la gestion des droits.
# ------------------------------------------------------------------------------

class Parametre(models.Model):
    """
    Définit un paramètre configurable de l'application.
    """
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
    """
    Stocke la valeur effective d'un paramètre, soit globalement, soit
    pour un centre spécifique.
    """
    parametre = models.ForeignKey(Parametre, on_delete=models.CASCADE, related_name='valeurs')
    valeur = models.CharField(max_length=255)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, null=True, blank=True, help_text="Si ce paramètre est spécifique à un centre")
    responsable = models.ForeignKey(Agent, on_delete=models.PROTECT, help_text="Agent responsable de cette valeur")
    est_global = models.BooleanField(default=False, help_text="Cochez si la valeur s'applique à tous les centres")

    class Meta:
        verbose_name = "Valeur de Paramètre"
        verbose_name_plural = "Valeurs de Paramètres"
        # Un paramètre ne peut avoir qu'une seule valeur globale
        # ou une seule valeur par centre.
        unique_together = ('parametre', 'centre')

    def __str__(self):
        scope = f"pour {self.centre.code_centre}" if self.centre else "global"
        return f"{self.parametre.nom} ({scope}) = {self.valeur}"

class Role(models.Model):
    """
    Définit un rôle fonctionnel dans l'application (ex: Admin, Chef de Salle).
    """
    nom = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"

    def __str__(self):
        return self.nom

class AgentRole(models.Model):
    """
    Table de liaison qui attribue un Rôle à un Agent. L'attribution
    peut être globale ou limitée à un Centre.
    """
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='roles_assignes')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='agents_assignes')
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, null=True, blank=True, help_text="Laisser vide si le rôle est global")

    class Meta:
        verbose_name = "Attribution de Rôle"
        verbose_name_plural = "Attributions de Rôles"
        unique_together = ('agent', 'role', 'centre')

    def __str__(self):
        scope = f" @ {self.centre.code_centre}" if self.centre else " (Global)"
        return f"{self.agent} a le rôle '{self.role}'{scope}"

# ==============================================================================
# SECTION IV : GESTION DOCUMENTAIRE
# ==============================================================================
# Modèles pour la gestion des documents, de leurs versions et des circuits
# de signature.
# ------------------------------------------------------------------------------

class DocumentType(models.Model):
    """
    Catégorise les documents (ex: Procédure, Manuel, Fiche Réflexe).
    """
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Type de Document"
        verbose_name_plural = "Types de Documents"

    def __str__(self):
        return self.nom

class Document(models.Model):
    """
    Représente un document officiel avec ses métadonnées et sa version en vigueur.
    """
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
    """
    Historique des différentes versions d'un document.
    """
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
    """
    Étape d'un circuit de validation pour un document.
    """
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
# Modèles pour tracer les demandes de changement, de la proposition à l'action.
# ------------------------------------------------------------------------------

class CentreRole(models.Model):
    """
    Définit un rôle spécifique au sein d'un centre (ex: Chef de salle, RSMS local).
    Similaire à AgentRole mais plus orienté fonctions locales.
    """
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
    """
    Désigne un agent comme étant Responsable du Management de la Sécurité (SMS).
    """
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='responsabilite_sms')
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Responsable SMS"
        verbose_name_plural = "Responsables SMS"

    def __str__(self):
        return f"Responsabilité SMS de {self.agent}"

class MRR(models.Model):
    """
    Fiche de suivi d'une exigence réglementaire ou d'une demande de modification.
    """
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
    """
    Signataire associé à une fiche MRR.
    """
    mrr = models.ForeignKey(MRR, on_delete=models.CASCADE, related_name='signataires')
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT)
    date_signature = models.DateField(null=True, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = ('mrr', 'agent')
        verbose_name = "Signataire MRR"
        verbose_name_plural = "Signataires MRR"
        
class MRRProgression(models.Model):
    """
    Journal de l'avancement d'une fiche MRR.
    """
    mrr = models.ForeignKey(MRR, on_delete=models.CASCADE, related_name='progression')
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=100)
    commentaire = models.TextField()
    
    class Meta:
        verbose_name = "Progression MRR"
        verbose_name_plural = "Progressions MRR"
        ordering = ['-date']

class Changement(models.Model):
    """
    Description d'un changement proposé, souvent lié à une MRR.
    """
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
    """
    Action concrète à réaliser pour implémenter un changement.
    """
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
    """
    Notification envoyée concernant une action (rappel, etc.).
    """
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
# Modèles dédiés au suivi des événements de sécurité, audits et recommandations.
# ------------------------------------------------------------------------------

class ResponsableQSCentral(models.Model):
    """
    Désigne l'agent en charge de la Qualité et Sécurité au niveau central.
    """
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='responsabilite_qs_central')
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Responsable QS Central"
        verbose_name_plural = "Responsables QS Central"

    def __str__(self):
        return f"Responsabilité QS Centrale de {self.agent}"

class EvenementQS(models.Model):
    """
    Fiche de signalement d'un événement de sécurité.
    """
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
    """
    Recommandation émise suite à l'analyse d'un événement ou d'un audit.
    """
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
    """
    Action concrète à réaliser pour implémenter une recommandation QS.
    """
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
    """
    Trace un audit de Qualité/Sécurité.
    """
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
    """
    Évaluation d'un risque identifié dans le cadre du SMS.
    """
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
    """
    Notification liée à une action QS.
    """
    STATUT_CHOICES = [('a_envoyer', 'À envoyer'), ('envoye', 'Envoyé'), ('erreur', 'Erreur')]
    
    action = models.ForeignKey(ActionQS, on_delete=models.CASCADE, related_name='notifications_qs')
    destinataire = models.CharField(max_length=255)
    date_envoi = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='a_envoyer')
    message = models.TextField()

    class Meta:
        verbose_name = "Notification QS"
        verbose_name_plural = "Notifications QS"