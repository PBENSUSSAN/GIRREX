# Fichier : core/admin.py

from django.contrib import admin
from .models import (
    # Section I: RH
    Centre, Agent, Licence, Qualification, Mention, CertificatMed,
    Module, Organisme, Formation, Evaluation, Habilitation, Affectation,

    # Section II: Vols
    Client, Vol, ControleVol, AuditHeuresControle,

    # Section III: Paramétrage
    Parametre, ValeurParametre, Role, AgentRole,

    # Section IV: Documentaire
    DocumentType, Document, DocumentVersion, SignatureCircuit,

    # Section V: Changement & MRR
    CentreRole, ResponsableSMS, MRR, MRRSignataire, MRRProgression,
    Changement, Action, Notification,

    # Section VI: QS/SMS
    ResponsableQSCentral, EvenementQS, RecommendationQS, ActionQS,
    AuditQS, EvaluationRisqueQS, NotificationQS,
)

# ==============================================================================
# SECTION I : GESTION DES RESSOURCES HUMAINES (RH)
# ==============================================================================

@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    list_display = ('nom_centre', 'code_centre')
    search_fields = ('nom_centre', 'code_centre')

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    # --- Configuration de la vue LISTE ---
    list_display = ('id_agent', 'reference', 'trigram', 'nom', 'prenom', 'centre', 'actif')
    list_filter = ('centre', 'actif', 'type_agent')
    search_fields = ('reference', 'trigram', 'nom', 'prenom', 'user__username')
    ordering = ('reference',)
    
    # --- Configuration du formulaire de MODIFICATION/AJOUT ---
    # On liste TOUS les champs du modèle, organisés en sections.
    fieldsets = (
        # Section 1: Identifiants principaux
        ('Identification Principale', {
            'fields': ('id_agent', 'reference', 'trigram')
        }),
        # Section 2: Compte et Affectation
        ('Compte & Affectation', {
            'fields': ('user', 'centre', 'actif', 'type_agent')
        }),
        # Section 3: Informations personnelles (repliée par défaut)
        ('Détails Personnels (optionnel)', {
            'classes': ('collapse',), # Rend la section repliable
            'fields': ('nom', 'prenom', 'date_naissance', 'nationalite'),
        }),
    )

    # Pour que les champs ForeignKey soient faciles à utiliser
    autocomplete_fields = ['user', 'centre']
    
    # Pour rendre le champ id_agent non modifiable après création
    # C'est une bonne pratique pour les ID legacy
    readonly_fields = ('id_agent',)

    # Pour un affichage plus compact
    radio_fields = {'type_agent': admin.HORIZONTAL}

@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display = ('num_licence', 'agent', 'type_licence', 'date_validite', 'statut')
    list_filter = ('statut', 'type_licence', 'date_validite')
    search_fields = ('num_licence', 'agent__trigram', 'agent__reference')
    autocomplete_fields = ['agent'] # Pour une recherche facile de l'agent

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('id_formation', 'agent', 'annee', 'duree', 'module')
    list_filter = ('annee', 'agent__centre')
    search_fields = ('agent__trigram', 'agent__reference', 'module__sujet')
    autocomplete_fields = ['agent', 'module']

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('id_module', 'module', 'item', 'sujet', 'module_type')
    list_filter = ('module_type', 'module')
    search_fields = ('sujet', 'item', 'precisions')

# Enregistrement des autres modèles RH avec une configuration par défaut
admin.site.register(Qualification)
admin.site.register(Mention)
admin.site.register(CertificatMed)
admin.site.register(Organisme)
admin.site.register(Evaluation)
admin.site.register(Habilitation)
admin.site.register(Affectation)


# ==============================================================================
# SECTION II : GESTION DES VOLS
# ==============================================================================

@admin.register(Vol)
class VolAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date_vol', 'type_vol', 'etat', 'centre', 'client')
    list_filter = ('etat', 'type_vol', 'centre', 'date_vol')
    search_fields = ('client__nom', 'centre__nom_centre', 'cca__trigram', 'cca__reference')
    autocomplete_fields = ['client', 'centre', 'cca']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact', 'email')
    search_fields = ('nom', 'contact', 'email')

# Enregistrement des autres modèles de cette section
admin.site.register(ControleVol)
admin.site.register(AuditHeuresControle)


# ==============================================================================
# SECTION III : PARAMETRAGE DYNAMIQUE ET GESTION DES ROLES
# ==============================================================================

admin.site.register(Parametre)
admin.site.register(ValeurParametre)
admin.site.register(Role)
admin.site.register(AgentRole)


# ==============================================================================
# SECTION IV : GESTION DOCUMENTAIRE
# ==============================================================================

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('titre', 'reference', 'type_document', 'date_mise_a_jour', 'est_archive')
    list_filter = ('type_document', 'est_archive', 'centres_visibles')
    search_fields = ('titre', 'reference', 'description')

admin.site.register(DocumentType)
admin.site.register(DocumentVersion)
admin.site.register(SignatureCircuit)


# ==============================================================================
# SECTION V : GESTION DU CHANGEMENT ET MRR
# ==============================================================================

@admin.register(MRR)
class MRRAdmin(admin.ModelAdmin):
    list_display = ('intitule', 'statut', 'date_ouverture', 'date_cloture')
    list_filter = ('statut',)
    search_fields = ('intitule',)

admin.site.register(CentreRole)
admin.site.register(ResponsableSMS)
admin.site.register(MRRSignataire)
admin.site.register(MRRProgression)
admin.site.register(Changement)
admin.site.register(Action)
admin.site.register(Notification)


# ==============================================================================
# SECTION VI : QUALITE/SECURITE DES VOLS (QS/SMS)
# ==============================================================================

@admin.register(EvenementQS)
class EvenementQSAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'centre', 'rapporteur', 'niveau_gravite', 'statut')
    list_filter = ('statut', 'niveau_gravite', 'centre')
    search_fields = ('description', 'analyse', 'rapporteur__trigram')

admin.site.register(ResponsableQSCentral)
admin.site.register(RecommendationQS)
admin.site.register(ActionQS)
admin.site.register(AuditQS)
admin.site.register(EvaluationRisqueQS)
admin.site.register(NotificationQS)