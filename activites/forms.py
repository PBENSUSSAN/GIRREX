# Fichier : activites/forms.py

from django import forms
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .models import Vol, SaisieActivite
from competences import services

class VolCreationForm(forms.ModelForm):
    """
    Formulaire pour la planification (création) d'un nouveau vol/mission.
    """
    class Meta:
        model = Vol
        fields = [
            'numero_strip', 'numero_commande', 'date_vol', 
            'heure_debut_prevue', 'duree_prevue', 'flux', 'indicatif'
        ]
        widgets = {
            'date_vol': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut_prevue': forms.TimeInput(attrs={'type': 'time'}),
            'duree_prevue': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'}),
        }

class VolRealisationForm(forms.ModelForm):
    """
    Formulaire simple pour saisir les heures réelles d'un segment de vol.
    """
    class Meta:
        model = Vol
        fields = ['heure_debut_reelle', 'heure_fin_reelle']
        widgets = {
            'heure_debut_reelle': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin_reelle': forms.TimeInput(attrs={'type': 'time'}),
        }
        labels = {
            'heure_debut_reelle': 'Début Réel',
            'heure_fin_reelle': 'Fin Réelle',
        }

class SaisieActiviteForm(forms.ModelForm):
    """
    Formulaire intelligent pour ajouter un participant à un segment de vol.
    Contient toute la logique de validation métier.
    """
    class Meta:
        model = SaisieActivite
        fields = ['agent', 'role']

    def __init__(self, *args, **kwargs):
        # La vue nous passera le 'vol' (le segment) lors de la création du formulaire.
        self.vol = kwargs.pop('vol', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        C'est ici que toute la magie de validation opère.
        """
        cleaned_data = super().clean()
        agent = cleaned_data.get('agent')
        role = cleaned_data.get('role')

        # Si les champs de base ne sont pas valides, ou si le vol n'est pas fourni, on s'arrête là.
        if not self.vol or not agent or not role:
            return cleaned_data
            
        # Règle 1: Un agent ne peut être assigné qu'une fois à un segment de vol.
        if SaisieActivite.objects.filter(vol=self.vol, agent=agent).exists():
            raise ValidationError(f"Cet agent est déjà assigné à ce segment de vol.")

        # Règle 2: Unicité du rôle actif (Contrôleur ou Stagiaire) par segment.
        if role in [SaisieActivite.Role.CONTROLEUR, SaisieActivite.Role.STAGIAIRE]:
            if SaisieActivite.objects.filter(vol=self.vol, role__in=[SaisieActivite.Role.CONTROLEUR, SaisieActivite.Role.STAGIAIRE]).exists():
                raise ValidationError("Un seul 'Contrôleur en Charge' ou 'Stagiaire' est autorisé par segment de vol.")
        
        # Règle 3 : Vérification de l'aptitude de l'agent via notre service.
        roles_a_verifier = [SaisieActivite.Role.CONTROLEUR, SaisieActivite.Role.STAGIAIRE, SaisieActivite.Role.ISP]
        if role in roles_a_verifier:
            try:
                est_apte, message_erreur = services.is_agent_apte_for_flux(
                    agent=agent, flux=self.vol.flux, on_date=self.vol.date_vol
                )
                if not est_apte:
                    raise ValidationError(f"Impossible d'assigner cet agent. Motif : {message_erreur}")
            except ObjectDoesNotExist:
                 raise ValidationError(f"Impossible d'assigner cet agent. Motif : Aucune MUA valide trouvée pour ce vol.")
        
        return cleaned_data