# Fichier : competences/models/__init__.py

# On importe les modèles depuis nos nouveaux fichiers.
# L'ordre a une importance pour la gestion des dépendances.

from .brevet import Brevet
from .qualification import Qualification
from .mua import MentionUniteAnnuelle
from .formation import MentionLinguistique, FormationReglementaire, SuiviFormationReglementaire, SuiviFormationContinue
from .evenement import EvenementCarriere
from .parametre import RegleDeRenouvellement

# Optionnel : Définir __all__ pour contrôler ce qui est importé avec "from .models import *"
__all__ = [
    'Brevet',
    'Qualification',
    'MentionUniteAnnuelle',
    'MentionLinguistique',
    'FormationReglementaire',
    'SuiviFormationReglementaire',
    'SuiviFormationContinue',
    'EvenementCarriere',
    'RegleDeRenouvellement',
]