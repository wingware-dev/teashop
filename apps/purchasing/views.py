from datetime import date, timedelta

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.decorators import owner_required
from apps.inventory.reorder import reorders

from . import reports, services


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def reorder(request):
    """Reorder levels for every item, and a button that drafts purchase
    orders for the low ones.  Drafting orders nothing: each draft waits
    for approval."""
    if request.method == "POST":
        result = services.draft_purchase_orders()
        if result.lines:
            messages.success(
                request,
                f"Drafted {len(result.lines)} line(s) on {len(result.orders)} purchase order(s).  "
                "Check them and approve each one; nothing is ordered until you do.",
            )
        else:
            messages.info(request, "Nothing new to draft.")
        if result.no_supplier:
            messages.warning(
                request,
                "No default supplier, so not drafted: " + ", ".join(r.item.name for r in result.no_supplier),
            )
        return redirect("purchasing:reorder")
    rows = sorted(reorders(), key=lambda r: (not r.needs_order, not r.is_low, r.item.name))
    return render(
        request,
        "purchasing/reorder.html",
        {
            "rows": rows,
            "to_order": [r for r in rows if r.needs_order and not r.made_here],
            "orders_url": reverse("admin:inventory_purchaseorder_changelist") + "?status__exact=draft",
        },
    )


@never_cache
@owner_required
def losses(request):
    months = 12
    rows, worst = reports.loss_trend(months)
    reasons = [(r, reports.R(r).label) for r in reports.LOSS_REASONS]
    table = [
        {"row": row, "loss_by_reason": [reports.money(row.by_reason.get(reason)) for reason, _ in reasons]}
        for row in rows
    ]
    return render(
        request,
        "purchasing/losses.html",
        {
            "table": table,
            "reasons": reasons,
            "worst": worst,
            "totals": {
                "loss": reports.money(sum((r.loss for r in rows), reports.ZERO)),
                "marketing": reports.money(sum((r.marketing for r in rows), reports.ZERO)),
                "personal": reports.money(sum((r.personal for r in rows), reports.ZERO)),
                "uncosted": sum(r.uncosted for r in rows),
            },
            "months": months,
        },
    )


def _date(value, default):
    try:
        return date.fromisoformat(value) if value else default
    except ValueError:
        return default


@never_cache
@owner_required
def profit(request):
    today = timezone.localdate()
    start = _date(request.GET.get("start"), today.replace(month=1, day=1))
    last = _date(request.GET.get("end"), today)
    if last < start:
        start, last = last, start
    end = last + timedelta(days=1)
    by_tea, by_size, total = reports.profitability(start, end)
    value, uncosted_lots = reports.stock_value()
    return render(
        request,
        "purchasing/profit.html",
        {
            "start": start,
            "end": last,
            "by_tea": by_tea,
            "by_size": by_size,
            "total": total,
            "marketing": reports.money(reports.marketing_cost(start, end)),
            "stock_value": value,
            "uncosted_lots": uncosted_lots,
        },
    )
