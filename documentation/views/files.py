# Fichier : documentation/views/files.py

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from ..models import Document

@login_required
def view_pdf_view(request, document_id):
    doc = get_object_or_404(Document, pk=document_id)
    try:
        return FileResponse(doc.fichier_pdf.open('rb'), as_attachment=False, content_type='application/pdf')
    except (FileNotFoundError, ValueError):
        raise Http404("Le fichier PDF n'a pas été trouvé ou est vide.")

@login_required
def download_pdf_view(request, document_id):
    doc = get_object_or_404(Document, pk=document_id)
    try:
        return FileResponse(doc.fichier_pdf.open('rb'), as_attachment=True)
    except (FileNotFoundError, ValueError):
        raise Http404("Le fichier PDF n'a pas été trouvé ou est vide.")