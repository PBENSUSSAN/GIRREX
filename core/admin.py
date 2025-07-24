# Fichier : core/admin.py (VERSION COMPLÈTE ET MISE À JOUR)

from django.contrib import admin
from .models import (
    # Section I: RH
    Centre, Agent, Licence, Qualification, Mention, CertificatMed, Module, Organisme, 
    Formation, Evaluation, Habilitation, Affectation,
    # Section II: Vols
    Client, Vol, ControleVol, AuditHeuresControle,
    # Section III: Paramétrage
    Parametre, ValeurParametre, Role, AgentRole, Delegation,
    # Section IV: Documentaire
    DocumentType, Document, DocumentVersion, SignatureCircuit,
    # Section V: Changement & MRR
    CentreRole, ResponsableSMS, MRR, MRRSignataire, MRRProgression, Changement, Action, 
    Notification,
    # Section VI: QS/SMS
    ResponsableQSCentral, EvenementQS, RecommendationQS, ActionQS, 
    AuditQS, EvaluationRisqueQS, NotificationQS,
    # Section VII : TDS
    PositionJour, TourDeService, TourDeServiceHistorique, VersionTourDeService,
    
    # ==========================================================================
    # IMPORTATION DES NOUVEAUX MODÈLES
    # ==========================================================================
    FeuilleTempsEntree, FeuilleTempsVerrou, FeuilleTempsCloture
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
    list_display = ('id_agent', 'reference', 'trigram', 'nom', 'prenom', 'centre', 'actif')
    list_filter = ('centre', 'actif', 'type_agent')
    search_fields = ('reference', 'trigram', 'nom', 'prenom', 'user__username')
    ordering = ('reference',)
    fieldsets = (
        ('Identification Principale', {'fields': ('id_agent', 'reference', 'trigram')}),
        ('Compte & Affectation', {'fields': ('user', 'centre', 'actif', 'type_agent')}),
        ('Détails Personnels (optionnel)', {'classes': ('collapse',), 'fields': ('nom', 'prenom', 'date_naissance', 'nationalite')}),
    )
    autocomplete_fields = ['user', 'centre']
    readonly_fields = ('id_agent',)
    radio_fields = {'type_agent': admin.HORIZONTAL}

@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display = ('num_licence', 'agent', 'type_licence', 'date_validite', 'statut')
    list_filter = ('statut', 'type_licence', 'date_validite')
    search_fields = ('num_licence', 'agent__trigram', 'agent__reference')
    autocomplete_fields = ['agent']

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

# Enregistrement simple pour les autres modèles de la section
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

admin.site.register(ControleVol)
admin.site.register(AuditHeuresControle)

# ==============================================================================
# SECTION III : PARAMETRAGE DYNAMIQUE ET GESTION DES ROLES
# ==============================================================================

admin.site.register(Parametre)
admin.site.register(ValeurParametre)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'scope', 'level')
    list_filter = ('scope', 'level')
    search_fields = ('nom',)
    filter_horizontal = ('groups',)

@admin.register(AgentRole)
class AgentRoleAdmin(admin.ModelAdmin):
    list_display = ('agent', 'role', 'centre', 'date_debut', 'date_fin')
    list_filter = ('role', 'centre', 'date_fin')
    search_fields = ('agent__trigram', 'agent__nom', 'role__nom')
    autocomplete_fields = ('agent', 'role', 'centre')

@admin.register(Delegation)
class DelegationAdmin(admin.ModelAdmin):
    list_display = ('delegant', 'delegataire', 'date_debut', 'date_fin', 'motivee_par')
    list_filter = ('date_debut', 'date_fin')
    search_fields = ('delegant__trigram', 'delegataire__trigram', 'motivee_par')
    autocomplete_fields = ('delegant', 'delegataire', 'creee_par')

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

# ==============================================================================
# SECTION VII : TDS
# ==============================================================================
@admin.register(PositionJour)
class PositionJourAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'centre', 'categorie')
    list_filter = ('centre', 'categorie')
    search_fields = ('nom', 'description')
    ordering = ('centre', 'nom')

@admin.register(TourDeService)
class TourDeServiceAdmin(admin.ModelAdmin):
    list_display = ('date', 'agent', 'position_matin', 'position_apres_midi', 'modifie_par')
    list_filter = ('date', 'agent__centre')
    search_fields = ('agent__trigram', 'agent__nom')
    autocomplete_fields = ['agent', 'position_matin', 'position_apres_midi']
    ordering = ('-date', 'agent')

@admin.register(TourDeServiceHistorique)
class TourDeServiceHistoriqueAdmin(admin.ModelAdmin):
    list_display = ('date', 'agent', 'type_modification', 'modifie_par', 'modifie_le')
    list_filter = ('type_modification', 'date')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(VersionTourDeService)
class VersionTourDeServiceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'valide_par', 'date_validation')
    list_filter = ('centre', 'annee', 'mois', 'valide_par')
    readonly_fields = ('centre', 'annee', 'mois', 'valide_par', 'date_validation', 'donnees_planning')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False

# ==============================================================================
# SECTION VIII : GESTION DES FEUILLES DE TEMPS
# ==============================================================================

@admin.register(FeuilleTempsEntree)
class FeuilleTempsEntreeAdmin(admin.ModelAdmin):
    """ Améliore l'affichage des entrées de feuille de temps dans l'admin. """
    list_display = ('agent', 'date_jour', 'heure_arrivee', 'heure_depart', 'modifie_par', 'modifie_le')
    list_filter = ('date_jour', 'agent__centre')
    search_fields = ('agent__trigram', 'agent__nom')
    date_hierarchy = 'date_jour'
    readonly_fields = ('modifie_le',)

@admin.register(FeuilleTempsVerrou)
class FeuilleTempsVerrouAdmin(admin.ModelAdmin):
    """ Permet de voir et de supprimer manuellement les verrous si nécessaire. """
    list_display = ('centre', 'chef_de_quart', 'verrouille_a')
    actions = ['supprimer_verrous_selectionnes']
    
    def supprimer_verrous_selectionnes(self, request, queryset):
        queryset.delete()
    supprimer_verrous_selectionnes.short_description = "Supprimer les verrous sélectionnés"

@admin.register(FeuilleTempsCloture)
class FeuilleTempsClotureAdmin(admin.ModelAdmin):
    """ Permet de visualiser les clôtures. """
    list_display = ('date_jour', 'centre', 'cloture_par', 'cloture_le', 'reouverte_par')
    list_filter = ('centre', 'date_jour')
    readonly_fields = ('cloture_par', 'cloture_le', 'reouverte_par', 'reouverte_le')