# Fichier : core/models/__init__.py

# On importe explicitement chaque modèle depuis les fichiers dédiés.
from .rh import Centre, Agent, Licence, Qualification, Mention, Module, Organisme, Formation, Evaluation, Habilitation, Affectation
from .vols import Client, Vol, ControleVol, AuditHeuresControle
from .parametrage import Parametre, ValeurParametre, Role, AgentRole, Delegation
#from .documentaire import DocumentType, Document, DocumentVersion, SignatureCircuit

from .planning import PositionJour, TourDeService, TourDeServiceHistorique, VersionTourDeService

# CORRECTION : On retire 'FeuilleTempsCloture' de cette ligne car le modèle n'existe plus.
from .feuille_temps import FeuilleTempsEntree, FeuilleTempsVerrou

# Importation des modèles séparés pour le cahier de marche
from .evenement import CategorieEvenement, EvenementCentre

# On importe ServiceJournalier ET ServiceJournalierHistorique depuis le même fichier.
from .service_journalier import ServiceJournalier, ServiceJournalierHistorique

# On importe les zones et leu activité
from .zone import Zone, ActiviteZone

from .medical import CertificatMed, RendezVousMedical