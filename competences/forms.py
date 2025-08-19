# Fichier : competences/forms.py

from django import forms
from .models import Licence, Qualification, MentionUnite

class LicenceForm(forms.ModelForm):
    """
    Formulaire pour la création et la modification de la licence d'un agent.
    """
    class Meta:
        model = Licence
        fields = ['numero_licence', 'date_delivrance', 'statut', 'motif_inaptitude', 'date_debut_inaptitude']
        widgets = {
            'date_delivrance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_debut_inaptitude': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motif_inaptitude': forms.Textarea(attrs={'rows': 3}),
        }

class QualificationForm(forms.ModelForm):
    """
    Formulaire pour ajouter une nouvelle qualification à une licence.
    """
    class Meta:
        model = Qualification
        fields = ['type_qualification', 'date_obtention', 'privileges_actifs']
        widgets = {
            'date_obtention': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'  # On spécifie le format attendu par l'input HTML5
            ),
        }
        labels = {
            'privileges_actifs': "L'agent exercera les privilèges liés à cette qualification (ISP/EXA)"
        }

class MentionUniteForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une mention d'unité locale.
    """
    class Meta:
        model = MentionUnite
        # ### CORRECTION ICI ###
        # On utilise le nouveau nom de champ 'qualification_source'
        fields = [
            'qualification_source', 'type_flux', 'mention_particuliere', 
            'date_delivrance', 'date_echeance', 'statut',
            'heures_requises_annuelles', 'date_debut_cycle'
        ]
        widgets = {
            'date_delivrance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_echeance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_debut_cycle': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        # On peut aussi ajouter un label plus clair pour l'utilisateur
        labels = {
            'qualification_source': "Qualification Associée"
        }

    def __init__(self, *args, **kwargs):
        licence = kwargs.pop('licence', None)
        super().__init__(*args, **kwargs)

        if licence:
            # ### CORRECTION ICI ###
            # On filtre le champ 'qualification_source'
            self.fields['qualification_source'].queryset = Qualification.objects.filter(licence=licence)