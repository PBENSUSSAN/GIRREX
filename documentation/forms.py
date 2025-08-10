# Fichier : documentation/forms.py
from django import forms
from .models import Document

class CreateDocumentForm(forms.ModelForm):
    """
    Formulaire pour la CRÉATION d'un document. Le fichier PDF est obligatoire.
    """
    class Meta:
        model = Document
        fields = [
            'reference', 'intitule', 'type_document', 
            'description', 'fichier_pdf', 'statut', 
            'date_mise_en_vigueur', 'periodicite_relecture_mois',
            'responsable_suivi', 'centres_applicables', 
            'remplace_document', 'document_parent'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date_mise_en_vigueur': forms.DateInput(attrs={'type': 'date'}),
            'centres_applicables': forms.CheckboxSelectMultiple,
        }

class UpdateDocumentForm(forms.ModelForm):
    """
    Formulaire pour la MODIFICATION d'un document. Le fichier PDF est optionnel.
    """
    class Meta:
        model = Document
        fields = [
            'reference', 'intitule', 'type_document', 
            'description', 'fichier_pdf', 'statut', 
            'date_mise_en_vigueur', 'periodicite_relecture_mois',
            'responsable_suivi', 'centres_applicables', 
            'remplace_document', 'document_parent'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date_mise_en_vigueur': forms.DateInput(attrs={'type': 'date'}),
            'centres_applicables': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On rend le champ fichier non-obligatoire pour la modification
        self.fields['fichier_pdf'].required = False