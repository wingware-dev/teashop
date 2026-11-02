"""The owner's report pages: sales, margin, New York sales tax, estimated
income tax, and the daily summaries sent to Wave."""

from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.decorators import owner_required

from . import accounting, sales, taxes
from .models import AccountingEntry


def _date(value, default):
    try:
        return date.fromisoformat(value) if value else default
    except ValueError:
        return default


def _period(request, default_start):
    """(start, last day, end) from ?start=&end=, both days included."""
    today = timezone.localdate()
    start = _date(request.GET.get("start"), default_start)
    last = _date(request.GET.get("end"), today)
    if last < start:
        start, last = last, start
    return start, last, last + timedelta(days=1)


@never_cache
@owner_required
def sales_report(request):
    today = timezone.localdate()
    start, last, end = _period(request, today.replace(month=1, day=1))
    by = request.GET.get("by") if request.GET.get("by") in sales.GROUPINGS else "month"
    if by == "day" and (end - start).days > 92:
        by = "week"
        messages.info(request, "Shown by week: by day is for three months or less.")
    rows, total = sales.by_period(start, end, by)
    products = sales.by_product(start, end)
    return render(request, "reports/sales.html", {
        "start": start, "end": last, "by": by, "groupings": sales.GROUPINGS.items(),
        "rows": rows, "total": total, "channels": sales.by_channel(start, end),
        "categories": sales.by_category(start, end), "products": products[:50],
        "more_products": max(len(products) - 50, 0),
    })


@never_cache
@owner_required
def margin_report(request):
    today = timezone.localdate()
    start, last, end = _period(request, today.replace(month=1, day=1))
    return render(request, "reports/margin.html", {"start": start, "end": last, "m": sales.margin(start, end)})


@never_cache
@owner_required
def sales_tax_report(request):
    today = timezone.localdate()
    quarters = taxes.ny_quarters(today)
    chosen = _date(request.GET.get("quarter"), None)
    period = taxes.ny_quarter(chosen) if chosen else quarters[0]
    # The annual filer's year (March to February) holding the chosen quarter.
    year_start = date(period.start.year if period.start.month >= 3 else period.start.year - 1, 3, 1)
    annual = request.GET.get("annual") == "1"
    if annual:
        end = date(year_start.year + 1, 3, 1)
        period = taxes.Period(year_start, end, f"Mar {year_start.year} to Feb {end.year}", end.replace(day=20))
    return render(request, "reports/sales_tax.html", {
        "period": period, "result": taxes.ny_sales_tax(period), "quarters": quarters, "annual": annual,
        "in_progress": period.end > today,
    })


@never_cache
@owner_required
def estimated_tax_report(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get("year", today.year))
    except ValueError:
        year = today.year
    year = min(max(year, 2020), today.year)
    return render(request, "reports/estimated_tax.html", {
        "year": year, "rows": taxes.estimated_tax(year, today), "years": range(today.year, today.year - 4, -1),
        "federal_rate": settings.ESTIMATED_TAX_FEDERAL_RATE * 100, "state_rate": settings.ESTIMATED_TAX_STATE_RATE * 100,
        "wage_base": settings.SOCIAL_SECURITY_WAGE_BASE,
    })


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def accounting_report(request):
    if request.method == "POST":
        from .jobs import accounting_summary

        accounting_summary.enqueue()
        messages.success(request, "Sending the days not yet posted.  Reload in a minute to see the result.")
        return redirect("reports:accounting")
    today = timezone.localdate()
    return render(request, "reports/accounting.html", {
        "entries": AccountingEntry.objects.all()[:60],
        "today": accounting.summary(today),
        "waiting": accounting.days_to_post(today),
        "fake": settings.WAVE_CLIENT != "wave",
    })
