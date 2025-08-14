# Fichier : es/forms.py

from django import forms
from .models import Changement, EtudeSecurite, EtapeEtude, CommentaireEtude
from core.models import Agent

class LancerChangementForm(forms.ModelForm):
    """
    Formulaire pour initier un nouveau processus de changement.
    """
    class Meta:
        model = Changement
        fields = [
            'titre',
            'description',
            'centre_principal',
            'correspondant_dircam',
            'fichier_notification_initiale'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'correspondant_dircam': 'Responsable ES National (Superviseur)',
            'fichier_notification_initiale': 'Formulaire de Notification (Annexe 1)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['correspondant_dircam'].queryset = Agent.objects.filter(actif=True).order_by('trigram')

class ClassifierChangementForm(forms.ModelForm):
    """
    Formulaire pour que le superviseur national classifie un changement.
    """
    type_etude_requise = forms.ChoiceField(
        choices=EtudeSecurite.TypeEtude.choices,
        label="Type d'étude de sécurité à mener",
        required=True,
        initial=EtudeSecurite.TypeEtude.DOSSIER_SECURITE,
        widget=forms.RadioSelect
    )
    
    class Meta:
        model = Changement
        fields = [
            'classification',
            'type_etude_requise',
            'fichier_reponse_notification'
        ]
        labels = {
            'classification': "Décision de classement",
            'fichier_reponse_notification': "Fichier de Réponse à Notification (Annexe 2)"
        }

# ==========================================================
#              DÉBUT DE L'AJOUT DES FORMULAIRES MANQUANTS
# ==========================================================
class UploadPreuveForm(forms.ModelForm):
    """
    Formulaire simple pour que l'ES Local uploade le document de preuve.
    """
    class Meta:
        model = EtapeEtude
        fields = ['document_preuve']
        labels = {
            'document_preuve': 'Document de preuve pour cette étape'
        }

class CommentaireForm(forms.ModelForm):
    """
    Formulaire simple pour ajouter un commentaire à une étude.
    """
    class Meta:
        model = CommentaireEtude
        fields = ['commentaire', 'piece_jointe']
        widgets = {
            'commentaire': forms.Textarea(attrs={'rows': 3}),
        }
# ==========================================================
#                FIN DE L'AJOUT DES FORMULAIRES MANQUANTS
# ==========================================================