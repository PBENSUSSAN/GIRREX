from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()

@register.simple_tag
def get_content_type_id(obj):
    """
    Template tag qui renvoie l'ID du ContentType pour un objet donné.
    """
    if not obj:
        return None
    return ContentType.objects.get_for_model(obj).pk