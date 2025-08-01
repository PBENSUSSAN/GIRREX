# Fichier : suivi/filters.py
import django_filters
from django.db.models import Q
from .models import Action, Centre

class ActionFilter(django_filters.FilterSet):
    # Filtre sur le titre ou la description (recherche partielle, insensible à la casse)
    recherche = django_filters.CharFilter(
        method='filter_by_recherche',
        label="Recherche (Titre, Desc.)"
    )

    # Ajout d'un filtre pour le tri, avec des labels clairs
    ordering = django_filters.OrderingFilter(
        fields=(
            ('echeance', 'echeance'),
            ('priorite', 'priorite'),
            ('statut', 'statut'),
            ('responsable', 'responsable'),
        ),
        field_labels={
            'echeance': 'Échéance',
            'priorite': 'Priorité',
            'statut': 'Statut',
            'responsable': 'Responsable',
        },
        label="Trier par"
    )

    class Meta:
        model = Action
        # On s'assure que TOUS les champs que l'on veut utiliser dans le formulaire sont listés ici.
        fields = ['recherche', 'categorie', 'statut', 'priorite', 'centre']

    def filter_by_recherche(self, queryset, name, value):
        # Cette méthode personnalisée est appelée par le filtre 'recherche'
        return queryset.filter(
            Q(titre__icontains=value) | Q(description__icontains=value)
        )