# Fichier : es/filters.py

import django_filters
from django import forms
from .models import EtudeSecurite

class EtudeSecuriteFilter(django_filters.FilterSet):
    # Champ de recherche textuelle
    titre = django_filters.CharFilter(
        field_name='changement__titre',
        lookup_expr='icontains',
        label="Recherche par Titre"
    )

    # Filtre par Statut (menu déroulant)
    statut = django_filters.ChoiceFilter(
        choices=EtudeSecurite.StatutEtude.choices,
        label="Statut de l'étude"
    )

    # Filtre par Avancement (avec des tranches logiques)
    AVANCEMENT_CHOICES = (
        ('0', 'Non débuté (0%)'),
        ('1-50', 'En cours (1-50%)'),
        ('51-99', 'Bien avancé (51-99%)'),
        ('100', 'Terminé (100%)'),
    )
    avancement_tranche = django_filters.ChoiceFilter(
        label="Avancement",
        choices=AVANCEMENT_CHOICES,
        method='filter_by_avancement'
    )

    class Meta:
        model = EtudeSecurite
        fields = ['titre', 'statut', 'avancement_tranche']

    def filter_by_avancement(self, queryset, name, value):
        if value == '0':
            return queryset.filter(avancement=0)
        elif value == '1-50':
            return queryset.filter(avancement__gte=1, avancement__lte=50)
        elif value == '51-99':
            return queryset.filter(avancement__gte=51, avancement__lte=99)
        elif value == '100':
            return queryset.filter(avancement=100)
        return queryset