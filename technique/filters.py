# Fichier : technique/filters.py

import django_filters
from django import forms
from .models import Miso, PanneCentre

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

class PanneFilter(django_filters.FilterSet):
    equipement_details = django_filters.CharFilter(
        field_name='equipement_details',
        lookup_expr='icontains',
        label="Recherche"
    )

    date_debut_apres = django_filters.DateFilter(
        field_name='date_heure_debut',
        lookup_expr='gte',
        label="Début après le",
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = PanneCentre
        fields = ['centre', 'type_equipement', 'criticite', 'statut']