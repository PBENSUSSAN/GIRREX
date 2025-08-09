# Fichier : technique/forms.py

from django import forms
from .models import Miso, PanneCentre, MisoHistorique # Assurez-vous que PanneCentre est bien importé

# Le formulaire PanneCentreForm reste inchangé
class PanneCentreForm(forms.ModelForm):
     
    commentaire_mise_a_jour = forms.CharField(
        label="Commentaire de mise à jour",
        required=False, # Le commentaire est optionnel
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Optionnel : décrivez la modification effectuée."
    )

    class Meta:
        model = PanneCentre
        # On utilise les nouveaux champs du modèle
        fields = [
            'type_equipement',
            'equipement_details',
            'date_heure_debut', 
            'criticite', 
            'description', 
            'notification_generale'
        ]
        widgets = {
            'date_heure_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }


# Le formulaire MisoForm est maintenant modifié
class MisoForm(forms.ModelForm):
    class Meta:
        model = Miso
        fields = [
            'centre', # On le garde ici pour les utilisateurs centraux
            'type_maintenance',
            'date_debut',
            'date_fin',
            'description',
            'piece_jointe',
        ]
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # --- NOUVELLE LOGIQUE D'ADAPTATION ---
        if user and hasattr(user, 'agent_profile') and user.agent_profile.centre:
            # Si l'utilisateur est local (a un centre de rattachement)
            # On retire le champ 'centre' du formulaire pour qu'il ne soit pas affiché
            self.fields.pop('centre', None)
        else:
            # Si l'utilisateur est central (pas de centre), le champ est obligatoire
            self.fields['centre'].required = True

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get("date_debut")
        date_fin = cleaned_data.get("date_fin")

        if date_debut and date_fin and date_fin <= date_debut:
            self.add_error('date_fin', "La date de fin doit être postérieure à la date de début.")
        
        return cleaned_data

class AnnulerMisoForm(forms.Form):
    motif_annulation = forms.CharField(
        label="Motif de l'annulation",
        widget=forms.Textarea(attrs={'rows': 4}),
        required=True,
        help_text="Veuillez expliquer pourquoi ce préavis est annulé."
    )