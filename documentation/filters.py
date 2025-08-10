# Fichier : documentation/filters.py
import django_filters
from core.models import Centre
from .models import Document, DocumentType
from django.db.models import Q

class DocumentFilter(django_filters.FilterSet):
    recherche_textuelle = django_filters.CharFilter(
        method='filter_by_text', 
        label="Recherche (Réf, Intitulé)"
    )

    type_document = django_filters.ModelChoiceFilter(
        queryset=DocumentType.objects.all(),
        label="Type de document"
    )
    
    centre = django_filters.ModelChoiceFilter(
        field_name='centres_applicables',
        queryset=Centre.objects.all(),
        label="Centre Concerné"
    )

    SCOPE_CHOICES = (('', 'Tous'), ('nationaux', 'Nationaux'), ('locaux', 'Locaux'),)
    scope = django_filters.ChoiceFilter(
        choices=SCOPE_CHOICES, 
        method='filter_by_scope', 
        label="Portée"
    )

    class Meta:
        model = Document
        fields = ['recherche_textuelle', 'type_document', 'scope', 'statut', 'centre']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if request and hasattr(request, 'centre_agent') and request.centre_agent:
            self.form.fields.pop('scope')
            self.form.fields.pop('centre')

    def filter_by_text(self, queryset, name, value):
        return queryset.filter(Q(reference__icontains=value) | Q(intitule__icontains=value))

    def filter_by_scope(self, queryset, name, value):
        if value == 'locaux':
            return queryset.filter(centres_applicables__isnull=False).distinct()
        if value == 'nationaux':
            return queryset.filter(centres_applicables__isnull=True)
        return queryset