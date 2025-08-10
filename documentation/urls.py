# Fichier : documentation/urls.py

from django.urls import path
from .views import consultation, gestion, files

app_name = 'documentation'

urlpatterns = [
    path('liste/', consultation.liste_documents_view, name='liste-documents'),
    path('detail/<int:document_id>/', consultation.detail_document_view, name='detail-document'),
    
    path('view/<int:document_id>/', files.view_pdf_view, name='view-pdf'),
    path('download/<int:document_id>/', files.download_pdf_view, name='download-pdf'),
    
    path('creer/', gestion.create_document_view, name='create-document'),
    path('modifier/<int:document_id>/', gestion.modifier_document_view, name='modifier-document'),
]