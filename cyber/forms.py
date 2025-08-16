# Fichier : cyber/forms.py

from django import forms
from .models import CyberRisque, CyberIncident, PieceJointe

class CyberRisqueForm(forms.ModelForm):
    """ Formulaire pour la modification d'un risque cyber. """
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Commentaire/Justification du changement",
        required=True,
        help_text="Expliquez la raison de la modification de ce risque."
    )

    class Meta:
        model = CyberRisque
        fields = ['description', 'gravite', 'probabilite', 'statut']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class CyberIncidentForm(forms.ModelForm):
    """ Formulaire pour la modification d'un incident cyber. """
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Commentaire/Justification du changement",
        required=True,
        help_text="Décrivez l'action en cours ou la raison de la modification."
    )

    class Meta:
        model = CyberIncident
        fields = ['date', 'description', 'statut']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class PieceJointeForm(forms.ModelForm):
    """ Formulaire DÉDIÉ à l'ajout d'une nouvelle pièce jointe. """
    class Meta:
        model = PieceJointe
        fields = ['fichier', 'description']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Description courte du fichier (optionnel)'}),
        }