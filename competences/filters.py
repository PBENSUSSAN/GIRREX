# Fichier : competences/filters.py

import django_filters
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from core.models import Agent, Centre

class CompetenceFilter(django_filters.FilterSet):
    recherche_agent = django_filters.CharFilter(
        field_name='trigram',
        lookup_expr='icontains',
        label="Rechercher un agent"
    )

    centre = django_filters.ModelChoiceFilter(
        queryset=Centre.objects.all(),
        label="Centre"
    )
    
    class Meta:
        model = Agent
        fields = ['recherche_agent', 'centre']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, 'agent_profile') and self.user.agent_profile.centre:
            if 'centre' in self.form.fields:
                self.form.fields.pop('centre')

    @property
    def form(self):
        # On récupère le formulaire une seule fois et on le stocke dans une variable locale 'form'
        form = super().form
        
        form.helper = FormHelper()
        form.helper.form_method = 'get'
        form.helper.form_class = 'row g-3 align-items-end'
        form.helper.form_show_labels = True
        form.helper.form_tag = False
        form.helper.disable_csrf = True

        # ==========================================================
        #                 LA CORRECTION EST ICI
        # ==========================================================
        # On utilise la variable locale 'form' et non plus 'self.form'
        # pour éviter la boucle de récursion.
        if 'centre' in form.fields:
            form.helper.layout = Layout(
                Row(
                    Column('recherche_agent', css_class='col-md'),
                    Column('centre', css_class='col-md'),
                    Column(Submit('submit', 'Filtrer', css_class='btn-primary w-100'), css_class='col-md-auto')
                )
            )
        else:
            form.helper.layout = Layout(
                Row(
                    Column('recherche_agent', css_class='col-md'),
                    Column(Submit('submit', 'Filtrer', css_class='btn-primary w-100'), css_class='col-md-auto')
                )
            )
            
        return form