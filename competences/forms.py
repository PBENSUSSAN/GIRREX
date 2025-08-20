# Fichier : competences/forms.py

from django import forms
from .models import Brevet, Qualification, EvenementCarriere

class BrevetForm(forms.ModelForm):
    """ Formulaire pour la création et la modification du brevet d'un agent. """
    class Meta:
        model = Brevet
        fields = ['numero_brevet', 'date_delivrance']
        widgets = {
            'date_delivrance': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
        }

class QualificationForm(forms.ModelForm):
    """ Formulaire pour ajouter une nouvelle qualification (un jalon de carrière). """
    class Meta:
        model = Qualification
        fields = ['centre', 'type_flux', 'type_qualification', 'date_obtention']
        widgets = {
            'date_obtention': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
        }

class EvenementCarriereForm(forms.ModelForm):
    """ Formulaire pour enregistrer une interruption de carrière. """
    class Meta:
        model = EvenementCarriere
        fields = ['type_evenement', 'date_debut', 'date_fin', 'details']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'details': forms.Textarea(attrs={'rows': 4}),
        }