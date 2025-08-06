# Fichier : documentation/urls.py

from django.urls import path
# On importe les modules de vues au lieu d'un seul fichier
from .views import consultation, gestion, files

app_name = 'documentation'

urlpatterns = [
    # URLs de consultation
    path('liste/', consultation.liste_documents_view, name='liste-documents'),
    path('detail/<int:document_id>/', consultation.detail_document_view, name='detail-document'),
    
    # URLs de gestion de fichier
    path('view/<int:version_id>/', files.view_pdf_view, name='view-pdf'),
    path('download/<int:version_id>/', files.download_pdf_view, name='download-pdf'),
    
    # URLs de création/modification
    path('document/<int:document_id>/add_version/', gestion.add_version_view, name='add-version'),
    path('creer/', gestion.create_document_view, name='create-document'),
]