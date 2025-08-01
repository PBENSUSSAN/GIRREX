# Fichier : suivi/forms.py
from django import forms
from .models import Action
from core.models import Agent, Centre

class CreateActionForm(forms.ModelForm):
    document_intitule = forms.CharField(label="Intitulé du document", required=False)
    piece_jointe = forms.FileField(label="Pièce jointe (PDF)", required=False)

    class Meta:
        model = Action
        fields = [
            'titre', 'description', 'categorie', 
            'document_intitule', 'piece_jointe',
            'responsable', 'centre', 'echeance', 'priorite'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'echeance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # ==================================================================
        # CORRECTION : On nettoie la liste des catégories
        # ==================================================================
        # On récupère les choix possibles pour le champ 'categorie'
        choices = self.fields['categorie'].choices
        # On crée une nouvelle liste de choix en excluant la catégorie interne
        filtered_choices = [choice for choice in choices if choice[0] != 'PRISE_EN_COMPTE_DOC']
        # On assigne cette nouvelle liste filtrée au champ du formulaire
        self.fields['categorie'].choices = filtered_choices
        # ==================================================================

        if user and hasattr(user, 'agent_profile'):
            agent = user.agent_profile
            self.fields['responsable'].initial = agent
            if agent.centre:
                self.fields['centre'].initial = agent.centre
                self.fields['centre'].disabled = True
                self.fields['responsable'].queryset = Agent.objects.filter(centre=agent.centre, actif=True).order_by('trigram')
            else:
                self.fields['responsable'].queryset = Agent.objects.filter(actif=True).order_by('trigram')
                self.fields['centre'].queryset = Centre.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        categorie = cleaned_data.get('categorie')
        piece_jointe = cleaned_data.get('piece_jointe')
        document_intitule = cleaned_data.get('document_intitule')

        if categorie == Action.CategorieAction.DIFFUSION_DOC:
            if not piece_jointe:
                self.add_error('piece_jointe', "Une pièce jointe est requise pour une diffusion documentaire.")
            if not document_intitule:
                self.add_error('document_intitule', "L'intitulé du document est requis pour une diffusion documentaire.")
        
        return cleaned_data

class UpdateActionForm(forms.ModelForm):
    """
    Formulaire pour permettre au responsable de mettre à jour le statut
    et l'avancement de son action.
    """
    # On ajoute un champ pour les commentaires de mise à jour
    update_comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Commentaire de mise à jour (optionnel)",
        required=False
    )

    class Meta:
        model = Action
        fields = ['statut', 'avancement']

class AddActionCommentForm(forms.Form):
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Ajouter un commentaire",
        help_text="Décrivez l'avancement ou l'action réalisée."
    )

class DiffusionCibleForm(forms.Form):
    centres = forms.ModelMultipleChoiceField(
        queryset=Centre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Sélectionnez les centres destinataires",
        required=True
    )