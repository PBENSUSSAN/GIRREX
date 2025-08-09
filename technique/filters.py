# Fichier : technique/filters.py

import django_filters
from django import forms
from .models import Miso

class MisoFilter(django_filters.FilterSet):
    # Champ de recherche textuelle sur la description
    description = django_filters.CharFilter(
        field_name='description',
        lookup_expr='icontains', # 'icontains' = recherche partielle insensible à la casse
        label="Recherche"
    )

    # Champ pour filtrer par date de début
    date_debut_apres = django_filters.DateFilter(
        field_name='date_debut',
        lookup_expr='gte', # 'gte' = greater than or equal to
        label="Début après le",
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Miso
        fields = ['centre', 'type_maintenance', 'statut_override']