# Fichier : documentation/forms.py
from django import forms
from .models import Document, VersionDocument

class AddVersionForm(forms.ModelForm):
    class Meta:
        model = VersionDocument
        fields = ['numero_version', 'fichier_pdf', 'commentaire_version']
        widgets = {
            'commentaire_version': forms.Textarea(attrs={'rows': 4}),
        }

class DocumentForm(forms.ModelForm):
    """
    Formulaire pour la création de la fiche principale d'un document.
    """
    class Meta:
        model = Document
        fields = [
            'reference', 'intitule', 'type_document', 
            'description', 'responsable_suivi', 
            'date_echeance_suivi', 'centres_applicables'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date_echeance_suivi': forms.DateInput(attrs={'type': 'date'}),
            'centres_applicables': forms.CheckboxSelectMultiple,
        }