# Fichier : suivi/filters.py (Version Finale et Définitive)

import django_filters
from django.db.models import Q
from .models import Action, Centre
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

class ActionFilter(django_filters.FilterSet):
    recherche = django_filters.CharFilter(
        method='filter_by_recherche',
        label="Recherche (Titre, Desc.)"
    )
    ordering = django_filters.OrderingFilter(
        fields=(('echeance', 'echeance'), ('priorite', 'priorite'), ('statut', 'statut'), ('responsable', 'responsable')),
        label="Trier par"
    )
    
    # ==========================================================
    #           LA CORRECTION DÉFINITIVE EST ICI
    # ==========================================================
    # On utilise ModelChoiceFilter pour un menu déroulant simple
    # qui est vide par défaut.
    centres = django_filters.ModelChoiceFilter(
        queryset=Centre.objects.all(),
        label="Centres Concernés"
    )

    class Meta:
        model = Action
        fields = ['recherche', 'categorie', 'statut', 'priorite', 'centres']

    def filter_by_recherche(self, queryset, name, value):
        return queryset.filter(Q(titre__icontains=value) | Q(description__icontains=value))

    # Le FormHelper est conservé car c'est la meilleure pratique pour la mise en page
    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.form_method = 'get'
        form.helper.form_class = 'row g-3 align-items-center'
        form.helper.form_show_labels = True
        form.helper.form_tag = False
        form.helper.disable_csrf = True

        form.helper.layout = Layout(
            Row(
                Column('recherche', css_class='col-md'),
                Column('categorie', css_class='col-md'),
                Column('statut', css_class='col-md'),
                Column('centres', css_class='col-md'), # Crispy affichera maintenant un menu déroulant standard
                Column('ordering', css_class='col-md'),
                Column(Submit('submit', 'Filtrer', css_class='btn-primary w-100'), css_class='col-md-auto')
            )
        )
        return form


class ArchiveFilter(django_filters.FilterSet):
    recherche = django_filters.CharFilter(
        method='filter_by_recherche',
        label="Recherche (Titre, Desc.)"
    )
    # CORRECTION DE LA SYNTAXE CI-DESSOUS
    ordering = django_filters.OrderingFilter(
        fields=(('echeance', 'echeance'), ('responsable', 'responsable')),
        field_labels={'echeance': 'Échéance', 'responsable': 'Responsable'},
        label="Trier par"
    )
    
    centres = django_filters.ModelChoiceFilter(
        field_name='centres', # On garde le nom du champ du modèle
        queryset=Centre.objects.all(),
        label="Centres Concernés"
    )
    
    class Meta:
        model = Action
        fields = ['recherche', 'categorie', 'centres']

    def filter_by_recherche(self, queryset, name, value):
        return queryset.filter(
            Q(titre__icontains=value) | Q(description__icontains=value)
        )