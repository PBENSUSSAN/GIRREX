# Fichier : es/urls.py (VERSION CORRIGÉE)

from django.urls import path
# ### CORRECTION ### : On importe explicitement les modules 'processus' et 'etude' depuis le dossier 'views'
from .views import processus, etude

app_name = 'es'

urlpatterns = [
    # URLs gérées par le module 'processus'
    path('tableau-bord/', processus.tableau_etudes_view, name='tableau-etudes'),
    path('lancer-changement/', processus.lancer_changement_view, name='lancer-changement'),
    path('changement/<int:changement_id>/detail/', processus.detail_changement_view, name='detail-changement'),
    path('changement/<int:changement_id>/classifier/', processus.classifier_changement_view, name='classifier-changement'),
    path('changements-a-classifier/', processus.liste_changements_view, name='liste-changements'),

    # URLs gérées par le module 'etude'
    path('etude/<int:etude_id>/detail/', etude.detail_etude_view, name='detail-etude'),
    path('etape/<int:etape_id>/uploader-preuve/', etude.uploader_preuve_view, name='uploader-preuve'),
    path('etape/<int:etape_id>/valider/', etude.valider_etape_view, name='valider-etape'),
    path('etude/<int:etude_id>/creer-action-formation/', etude.creer_action_formation_view, name='creer-action-formation'),
]