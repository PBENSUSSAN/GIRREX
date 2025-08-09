# Fichier : technique/urls.py

from django.urls import path
# On importe bien le module "miso" depuis notre dossier "views"
from .views import miso

app_name = 'technique'

urlpatterns = [
    # On préfixe maintenant les fonctions avec "miso." au lieu de "views."
    path('miso/liste/', miso.liste_miso_view, name='liste-miso'),
    path('miso/creer/', miso.creer_miso_view, name='creer-miso'),
    path('miso/<int:miso_id>/modifier/', miso.modifier_miso_view, name='modifier-miso'),
    path('miso/<int:miso_id>/annuler/', miso.annuler_miso_view, name='annuler-miso'),
    path('miso/archives/', miso.archives_miso_view, name='archives-miso'),
]