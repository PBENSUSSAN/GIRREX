# Fichier : documentation/urls.py (Version finale avec double fonctionnalité)

from django.urls import path
from . import views

app_name = 'documentation'

urlpatterns = [
    # URLs de consultation
    path('liste/', views.liste_documents_view, name='liste-documents'),
    path('detail/<int:document_id>/', views.detail_document_view, name='detail-document'),
    
    # URLs de gestion de fichier
    path('view/<int:version_id>/', views.view_pdf_view, name='view-pdf'),
    path('download/<int:version_id>/', views.download_pdf_view, name='download-pdf'),
    path('document/<int:document_id>/add_version/', views.add_version_view, name='add-version'),
]