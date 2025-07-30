# Fichier : documentation/forms.py
from django import forms
from .models import VersionDocument

class AddVersionForm(forms.ModelForm):
    class Meta:
        model = VersionDocument
        fields = ['numero_version', 'fichier_pdf', 'commentaire_version']
        widgets = {
            'commentaire_version': forms.Textarea(attrs={'rows': 4}),
        }