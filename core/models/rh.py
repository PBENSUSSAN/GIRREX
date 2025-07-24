# Fichier : core/models/rh.py
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone

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