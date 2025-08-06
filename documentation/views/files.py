# Fichier : documentation/views/files.py

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from ..models import VersionDocument

@login_required
def view_pdf_view(request, version_id):
    """ Sert le fichier PDF pour qu'il soit affiché ("inline") dans le navigateur. """
    version = get_object_or_404(VersionDocument, pk=version_id)
    try:
        return FileResponse(version.fichier_pdf.open('rb'), as_attachment=False, content_type='application/pdf')
    except FileNotFoundError:
        raise Http404("Le fichier PDF n'a pas été trouvé sur le serveur.")

@login_required
def download_pdf_view(request, version_id):
    """ Sert le fichier PDF pour forcer son téléchargement ("attachment"). """
    version = get_object_or_404(VersionDocument, pk=version_id)
    try:
        return FileResponse(version.fichier_pdf.open('rb'), as_attachment=True, content_type='application/pdf')
    except FileNotFoundError:
        raise Http404("Le fichier PDF n'a pas été trouvé sur le serveur.")