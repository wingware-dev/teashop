"""The owner's AI agents page: this month's spending against the cap, which
agents use the real AI service, and everything the agents did lately."""

from django.conf import settings
from django.db.models import Count, Sum
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from apps.audit.models import AuditEvent
from apps.core.decorators import owner_required

from . import budget
from .models import AIUsage


@never_cache
@owner_required
def owner_home(request):
    spent, cap = budget.spent_this_month(), budget.cap()
    by_agent = (AIUsage.objects.filter(at__gte=budget.month_start()).values("agent")
                .annotate(calls=Count("pk"), cost=Sum("cost"), input=Sum("input_tokens"), output=Sum("output_tokens"))
                .order_by("agent"))
    agents = sorted({row["agent"] for row in by_agent} | set(settings.AGENTS_LIVE))
    rows = {row["agent"]: row for row in by_agent}
    return render(request, "agents/owner_home.html", {
        "spent": spent, "cap": cap, "remaining": budget.remaining(),
        "percent": int(spent * 100 / cap) if cap else 100,
        "agents": [(name, name in settings.AGENTS_LIVE, rows.get(name)) for name in agents],
        "model": settings.AGENTS_MODEL,
        "prices": settings.AGENTS_PRICE_PER_MTOK,
        "events": AuditEvent.objects.filter(actor_type=AuditEvent.ActorType.AGENT)[:100],
    })
