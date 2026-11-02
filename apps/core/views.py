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
    """The owner's home page: the "Needs your attention" queue grouped by
    kind, each with its deadline, the latest deploy, backup and
    restore-test results, and recent audit events."""
    recent_events = AuditEvent.objects.all()[:25]
    # From the apps' providers (attention.py): orders, stock, failed jobs...
    entries = attention.queue()
    return render(
        request,
        "core/owner_dashboard.html",
        {
            "ops": ops_status(),
            "attention_groups": attention.grouped(entries),
            "overdue_count": sum(1 for entry in entries if entry.overdue),
            "shortcuts": attention.shortcuts(),
            "recent_events": recent_events,
            "admin_url": "/" + settings.ADMIN_URL,
            "version": settings.GIT_SHA,
        },
    )
