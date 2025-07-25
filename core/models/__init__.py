# Fichier : core/models/__init__.py

# On importe explicitement chaque modèle depuis nos nouveaux fichiers.
from .rh import Centre, Agent, Licence, Qualification, Mention, CertificatMed, Module, Organisme, Formation, Evaluation, Habilitation, Affectation
from .vols import Client, Vol, ControleVol, AuditHeuresControle
from .parametrage import Parametre, ValeurParametre, Role, AgentRole, Delegation
from .documentaire import DocumentType, Document, DocumentVersion, SignatureCircuit
from .mrr import CentreRole, ResponsableSMS, MRR, MRRSignataire, MRRProgression, Changement, Action, Notification
from .qualite import ResponsableQSCentral, EvenementQS, RecommendationQS, ActionQS, AuditQS, EvaluationRisqueQS, NotificationQS
from .planning import PositionJour, TourDeService, TourDeServiceHistorique, VersionTourDeService
from .feuille_temps import FeuilleTempsEntree, FeuilleTempsVerrou, FeuilleTempsCloture

# Importation des nouveaux modèles séparés
from .panne import PanneCentre
from .evenement import CategorieEvenement, EvenementCentre
from .service_journalier import ServiceJournalier