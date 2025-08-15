# Fichier : es/forms.py

from django import forms
from .models import Changement, EtudeSecurite, EtapeEtude, CommentaireEtude, MRR
from core.models import Agent
from suivi.models import Action

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

class UploadPreuveForm(forms.ModelForm):
    """
    Formulaire pour que l'ES Local uploade le document de preuve et liste les MRR.
    """
    class Meta:
        model = EtapeEtude
        fields = ['document_preuve', 'mrr_identifies']
        labels = {
            'document_preuve': 'Document de preuve pour cette étape',
            'mrr_identifies': 'Moyens en Réduction de Risque (MRR) identifiés'
        }
        widgets = {
            'mrr_identifies': forms.Textarea(attrs={'rows': 5}),
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

class MRRForm(forms.ModelForm):
    """
    Formulaire pour la création d'un nouveau Moyen en Réduction de Risque.
    """
    class Meta:
        model = MRR
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Décrire le moyen en réduction de risque...'}),
        }
        labels = {
            'description': ""
        }

class ActionFormationForm(forms.ModelForm):
    """
    Formulaire pour créer une action de suivi de type 'Formation'.
    """
    class Meta:
        model = Action
        fields = ['titre', 'description', 'responsable', 'echeance', 'priorite']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'echeance': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = Agent.objects.filter(actif=True).order_by('trigram')

class UpdateEtudeForm(forms.ModelForm):
    """
    Formulaire pour permettre aux responsables de piloter une étude de sécurité.
    """
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Commentaire de mise à jour / Justification",
        required=False
    )
    piece_jointe = forms.FileField(
        label="Pièce jointe (optionnel)",
        required=False
    )
    class Meta:
        model = EtudeSecurite
        fields = ['statut', 'avancement']