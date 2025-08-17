# Fichier : feedback/forms.py

from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['titre', 'description', 'categorie', 'module_concerne']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'titre': "Titre de votre demande",
            'description': "Décrivez votre remarque le plus précisément possible",
            'categorie': "Catégorie de la demande",
            'module_concerne': "Module de l'application concerné"
        }