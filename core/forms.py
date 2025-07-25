# Fichier : core/forms.py

from django import forms
from .models import PanneCentre, EvenementCentre, CategorieEvenement

class PanneCentreForm(forms.ModelForm):
    class Meta:
        model = PanneCentre
        fields = [
            'equipement_concerne', 
            'date_heure_debut', 
            'criticite', 
            'description', 
            'notification_generale'
        ]
        widgets = {
            'date_heure_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class EvenementCentreForm(forms.ModelForm):
    categorie = forms.ModelChoiceField(
        queryset=CategorieEvenement.objects.all(),
        label="Catégorie",
        help_text="Choisissez la catégorie la plus appropriée."
    )

    class Meta:
        model = EvenementCentre
        fields = [
            'titre', 
            'date_heure_evenement', 
            'categorie', 
            'description', 
            'notification_generale'
        ]
        widgets = {
            'date_heure_evenement': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        centre = kwargs.pop('centre', None)
        super().__init__(*args, **kwargs)
        if centre:
            self.fields['categorie'].queryset = CategorieEvenement.objects.filter(centre=centre)