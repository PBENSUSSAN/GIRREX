# Fichier : core/forms.py

from django import forms
from .models import EvenementCentre, CategorieEvenement, RendezVousMedical, CertificatMed, IndisponibiliteCabine, ArretMaladie

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
            'commentaire'
        ]
        widgets = {
            'date_heure_rdv': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'organisme_medical': forms.TextInput(attrs={'class': 'form-control'}),
            'type_visite': forms.TextInput(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
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


class ArretMaladieForm(forms.ModelForm):
    """
    Formulaire pour déclarer un arrêt maladie.
    """
    class Meta:
        model = ArretMaladie
        fields = [
            'date_debut',
            'date_fin_prevue',
            'motif',
            'certificat_arret'
        ]
        widgets = {
            'date_debut': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'date_fin_prevue': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'motif': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ex: Grippe, Congé maladie'}
            ),
        }
        labels = {
            'date_debut': 'Date de début',
            'date_fin_prevue': 'Date de fin prévue',
            'motif': 'Motif (optionnel)',
            'certificat_arret': 'Certificat médical (optionnel)'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin_prevue = cleaned_data.get('date_fin_prevue')
        
        # Vérifier que la date de fin est après la date de début
        if date_debut and date_fin_prevue:
            if date_fin_prevue < date_debut:
                self.add_error(
                    'date_fin_prevue',
                    "La date de fin doit être postérieure à la date de début."
                )
        
        return cleaned_data
