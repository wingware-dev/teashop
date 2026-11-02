"""The site's URLs plus uploaded media, for browser tests: the live test
server runs with DEBUG off, so it would not serve product photos."""

from django.conf import settings
from django.urls import re_path
from django.views.static import serve

from config.urls import urlpatterns as site_urlpatterns

def serve_media(request, path):
    # MEDIA_ROOT read per request, since tests point it at a temporary folder.
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    re_path(r"^media/(?P<path>.*)$", serve_media),
    *site_urlpatterns,
]
