# Fichier : documentation/filters.py
import django_filters
from .models import Document, DocumentType
from django.db.models import Q

class DocumentFilter(django_filters.FilterSet):
    # Filtre textuel sur l'intitulé ou la référence (recherche partielle)
    recherche_textuelle = django_filters.CharFilter(
        method='filter_by_text', 
        label="Recherche (Réf, Intitulé)"
    )

    # Filtre sur le type de document (rendu comme une liste déroulante)
    type_document = django_filters.ModelChoiceFilter(
        queryset=DocumentType.objects.all(),
        label="Type de document"
    )

    # Filtre personnalisé pour la portée "Nationale" vs "Locale"
    SCOPE_CHOICES = (
        ('', 'Tous'), # Option par défaut
        ('nationaux', 'Nationaux'),
        ('locaux', 'Locaux'),
    )
    scope = django_filters.ChoiceFilter(
        choices=SCOPE_CHOICES, 
        method='filter_by_scope', 
        label="Portée"
    )

    class Meta:
        model = Document
        # On ne met ici que les filtres simples. Les filtres complexes
        # sont déclarés au-dessus.
        fields = ['recherche_textuelle', 'type_document', 'scope']

    def filter_by_text(self, queryset, name, value):
        # Cette méthode est appelée quand le champ 'recherche_textuelle' est utilisé
        return queryset.filter(
            Q(reference__icontains=value) | Q(intitule__icontains=value)
        )

    def filter_by_scope(self, queryset, name, value):
        # Cette méthode est appelée pour notre filtre de portée
        if value == 'locaux':
            # Un document est "local" s'il est lié à au moins un centre.
            return queryset.filter(centres_applicables__isnull=False).distinct()
        if value == 'nationaux':
            # Un document est "national" s'il n'est lié à aucun centre.
            return queryset.filter(centres_applicables__isnull=True)
        return queryset