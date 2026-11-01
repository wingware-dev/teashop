import mimetypes
import os
from urllib.parse import unquote

from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

from apps.core.decorators import owner_required

from . import tracing
from .models import Lot, LotDocument

# Shown in the browser; anything else is downloaded, so an uploaded file
# can never run as a page on the shop's domain.
INLINE_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp", "text/plain"}


@never_cache
@owner_required
def private_file(request, name):
    """A supplier document or packing slip from private storage."""
    # The storage the file fields hold (made when the models were loaded).
    storage = LotDocument._meta.get_field("file").storage
    name = unquote(name)
    try:
        if not storage.exists(name):
            raise Http404("No such file")
        handle = storage.open(name, "rb")
    except SuspiciousFileOperation:
        raise Http404("No such file") from None
    base = os.path.basename(name)
    content_type = mimetypes.guess_type(base)[0] or "application/octet-stream"
    response = FileResponse(handle, as_attachment=content_type not in INLINE_TYPES, filename=base, content_type=content_type)
    response["Content-Security-Policy"] = "sandbox; default-src 'none'; img-src 'self'; style-src 'unsafe-inline'"
    response["Cache-Control"] = "private, no-store"
    return response


@never_cache
@owner_required
def lot_trace(request, pk):
    """Printable recall report for one lot."""
    lot = get_object_or_404(Lot.objects.select_related("item", "supplier"), pk=pk)
    context = {"trace": tracing.trace(lot), "lot": lot, "on_hand": lot.format_quantity(lot.quantity_on_hand)}
    return render(request, "inventory/lot_trace.html", context)
