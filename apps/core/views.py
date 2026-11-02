import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from apps.audit.models import AuditEvent
from apps.audit.ops import ops_status

from . import attention
from .decorators import owner_required

log = logging.getLogger(__name__)


@never_cache
def healthz(request):
    """Health check for Docker, the deploy script and uptime monitors.

    Returns 200 when the app can reach its database, else 503.  Says
    nothing that would help an attacker beyond the deployed version.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        log.exception("Health check: database unreachable")
        return JsonResponse({"status": "error", "database": "unreachable", "version": settings.GIT_SHA}, status=503)
    return JsonResponse({"status": "ok", "database": "ok", "version": settings.GIT_SHA})


@never_cache
@owner_required
def owner_dashboard(request):
    """The owner's home page.  Later phases add the "needs your attention"
    queue here; for now it shows the latest deploy, backup and restore-test
    results and recent audit events."""
    recent_events = AuditEvent.objects.all()[:25]
    ops = ops_status()
    return render(
        request,
        "core/owner_dashboard.html",
        {
            "ops": ops,
            "ops_problems": [status for status in ops if status.needs_attention],
            # From the feature apps' providers (attention.py): stock, organic sales...
            "attention_items": attention.collect(),
            "shortcuts": attention.shortcuts(),
            "recent_events": recent_events,
            "admin_url": "/" + settings.ADMIN_URL,
            "version": settings.GIT_SHA,
        },
    )
