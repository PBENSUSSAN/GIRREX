# Fichier : suivi/forms.py (Version Finale avec Formulaire de Diffusion Flexible)

from django import forms
from .models import Action
from core.models import Agent, Centre

# ==============================================================================
# FORMULAIRE DE DIFFUSION FLEXIBLE
# ==============================================================================
class DiffusionForm(forms.Form):
    """
    Formulaire générique et flexible pour paramétrer tous les scénarios de diffusion.
    """
    TYPE_DIFFUSION_CHOICES = [
        ('ACTION', "Pour Action (créer des tâches de suivi)"),
        ('INFO', "Pour Information (ne crée aucune tâche)"),
    ]

    # Scénario 3 & 2 : Diffusion par centre(s)
    centres_cibles = forms.ModelMultipleChoiceField(
        queryset=Centre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Diffuser via les responsables locaux des centres suivants :",
        required=False,
        help_text="Chaque responsable local recevra une tâche pour dispatcher à ses équipes."
    )
    
    # Option pour le Scénario 2
    diffusion_directe_agents = forms.BooleanField(
        label="Diffuser directement à tous les agents concernés (sans passer par l'intermédiaire local)",
        required=False
    )

    # Scénario 1 : Diffusion par agent(s) spécifique(s)
    agents_cibles = forms.ModelMultipleChoiceField(
        queryset=Agent.objects.filter(actif=True).order_by('trigram'),
        label="OU diffuser directement à des agents spécifiques :",
        required=False,
        help_text="Utilisez ce champ pour une diffusion ciblée, quel que soit le centre."
    )

    # Choix final : Action ou Information
    type_diffusion = forms.ChoiceField(
        choices=TYPE_DIFFUSION_CHOICES,
        widget=forms.RadioSelect,
        label="Type de diffusion",
        initial='ACTION'
    )

    def clean(self):
        """
        Vérifie que l'utilisateur a bien sélectionné au moins une cible.
        """
        cleaned_data = super().clean()
        centres_cibles = cleaned_data.get('centres_cibles')
        agents_cibles = cleaned_data.get('agents_cibles')

        if not centres_cibles and not agents_cibles:
            raise forms.ValidationError(
                "Vous devez sélectionner au moins un centre ou un agent destinataire."
            )
        
        return cleaned_data


# ==============================================================================
# AUTRES FORMULAIRES (CONSERVÉS À L'IDENTIQUE)
# ==============================================================================
class CreateActionForm(forms.ModelForm):
    document_intitule = forms.CharField(label="Intitulé du document", required=False)
    piece_jointe = forms.FileField(label="Pièce jointe (PDF)", required=False)

    class Meta:
        model = Action
        fields = [
            'titre', 'description', 'categorie', 
            'document_intitule', 'piece_jointe',
            'responsable', 'centres', 'echeance', 'priorite'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'echeance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'centres': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        choices = self.fields['categorie'].choices
        filtered_choices = [choice for choice in choices if choice[0] != 'PRISE_EN_COMPTE_DOC']
        self.fields['categorie'].choices = filtered_choices
        
        if user and hasattr(user, 'agent_profile'):
            agent = user.agent_profile
            self.fields['responsable'].initial = agent
            if agent.centre:
                self.fields['centres'].initial = [agent.centre]
                self.fields['responsable'].queryset = Agent.objects.filter(centre=agent.centre, actif=True).order_by('trigram')
            else:
                self.fields['responsable'].queryset = Agent.objects.filter(actif=True).order_by('trigram')
                self.fields['centres'].queryset = Centre.objects.all()

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