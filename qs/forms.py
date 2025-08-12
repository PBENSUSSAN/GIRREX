# Fichier : qs/forms.py

from django import forms
from core.models import Agent
from .models import FNE, DossierEvenement, RapportExterne

class PreDeclarationFNEForm(forms.Form):
    """
    Formulaire simple et dédié pour la pré-déclaration d'un événement
    par le Chef de Quart depuis le Cahier de Marche.
    """
    agent_implique = forms.ModelChoiceField(
        queryset=Agent.objects.none(),  # Le queryset sera défini dynamiquement dans la vue
        label="Agent impliqué dans l'événement",
        help_text="Sélectionnez l'agent qui a remonté ou vécu l'événement.",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    description = forms.CharField(
        label="Description sommaire de l'événement",
        help_text="Décrivez brièvement les faits. Les détails seront ajoutés plus tard.",
        widget=forms.Textarea(attrs={'rows': 4})
    )

    def __init__(self, *args, **kwargs):
        # On récupère le centre passé en paramètre depuis la vue
        centre = kwargs.pop('centre', None)
        super().__init__(*args, **kwargs)

        # Si un centre a été fourni, on met à jour le queryset du champ 'agent_implique'
        # pour ne montrer que les agents actifs de ce centre.
        if centre:
            self.fields['agent_implique'].queryset = Agent.objects.filter(
                centre=centre, 
                actif=True
            ).order_by('trigram')

class FNEUpdateOasisForm(forms.ModelForm):
    """
    Formulaire pour que le QS Local renseigne les informations
    une fois la déclaration faite dans OASIS.
    """
    class Meta:
        model = FNE
        fields = ['numero_oasis', 'date_declaration_oasis']
        widgets = {
             'date_declaration_oasis': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}, 
                format='%Y-%m-%d'
             ),    
        }

class FNEClotureForm(forms.ModelForm):
    """
    Formulaire pour que le QS Local finalise le dossier en
    uploadant le rapport et en définissant la classification.
    """
    class Meta:
        model = FNE
        fields = [
            'rapport_cloture_pdf',
            'classification_gravite_atm',
            'classification_gravite_ats',
            'classification_probabilite',
            'presente_en_cdsa_cmsa',
            'type_cloture'
        ]
        # Ici, nous pourrions ajouter des widgets de type 'Select' pour les classifications
        # une fois que vous m'aurez donné les choix possibles. Pour l'instant, des champs
        # textes simples suffiront.

class RegrouperFNEForm(forms.Form):
    """
    Formulaire pour sélectionner une ou plusieurs FNE à regrouper.
    """
    fne_a_regrouper = forms.ModelMultipleChoiceField(
        queryset=FNE.objects.filter(dossier__statut_global=DossierEvenement.Statut.OUVERT),
        widget=forms.CheckboxSelectMultiple,
        label="Sélectionnez les FNE à regrouper avec la FNE actuelle",
        required=True
    )

    def __init__(self, *args, **kwargs):
        # On retire la FNE de départ de la liste des choix pour éviter de la sélectionner
        fne_principale = kwargs.pop('fne_principale', None)
        super().__init__(*args, **kwargs)
        if fne_principale:
            self.fields['fne_a_regrouper'].queryset = self.fields['fne_a_regrouper'].queryset.exclude(pk=fne_principale.pk)

class RapportExterneForm(forms.ModelForm):
    class Meta:
        model = RapportExterne
        fields = ['organisme_source', 'reference_externe', 'date_reception', 'description', 'fichier_joint']
        widgets = {
            'date_reception': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3})
        }