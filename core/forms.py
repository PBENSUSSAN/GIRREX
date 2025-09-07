# Fichier : core/forms.py

from django import forms
from .models import EvenementCentre, CategorieEvenement, RendezVousMedical, CertificatMed, IndisponibiliteCabine

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

class RendezVousMedicalForm(forms.ModelForm):
    class Meta:
        model = RendezVousMedical
        fields = [
            'date_heure_rdv', 
            'organisme_medical', 
            'type_visite', 
            'statut'
        ]
        widgets = {
            'date_heure_rdv': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

class CertificatMedForm(forms.ModelForm):
    class Meta:
        model = CertificatMed
        fields = [
            'date_visite',
            'organisme_medical',
            'resultat',
            'classe_aptitude',
            'date_expiration_aptitude',
            'restrictions',
            'commentaire',
            'piece_jointe'
        ]
        widgets = {
            'date_visite': forms.DateInput(attrs={'type': 'date'}),
            'date_expiration_aptitude': forms.DateInput(attrs={'type': 'date'}),
            'restrictions': forms.Textarea(attrs={'rows': 2}),
            'commentaire': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        resultat = cleaned_data.get('resultat')
        date_expiration = cleaned_data.get('date_expiration_aptitude')

        # On s'assure que si l'agent est "Apte", une date d'expiration est fournie.
        if resultat == 'APTE' and not date_expiration:
            self.add_error('date_expiration_aptitude', "Une date d'expiration est requise si l'agent est déclaré apte.")
        
        return cleaned_data

class IndisponibiliteCabineForm(forms.ModelForm):
    """
    Formulaire pour déclarer une période d'indisponibilité pour une cabine.
    """
    class Meta:
        model = IndisponibiliteCabine
        fields = ['nom_cabine', 'date_jour', 'heure_debut', 'heure_fin', 'motif']
        widgets = {
            'date_jour': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time'}),
        }
