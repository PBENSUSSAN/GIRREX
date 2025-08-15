# Fichier : cyber/filters.py (NOUVEAU FICHIER)

import django_filters
from .models import CyberRisque, CyberIncident

class CyberRisqueFilter(django_filters.FilterSet):
    description = django_filters.CharFilter(
        lookup_expr='icontains',
        label="Recherche par description"
    )

    class Meta:
        model = CyberRisque
        fields = ['statut', 'gravite', 'probabilite']

class CyberIncidentFilter(django_filters.FilterSet):
    description = django_filters.CharFilter(
        lookup_expr='icontains',
        label="Recherche par description"
    )

    class Meta:
        model = CyberIncident
        fields = ['statut']