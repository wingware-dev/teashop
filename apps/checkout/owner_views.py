"""Back-office pages for checkout: sales by state against the nexus
thresholds, and New York sales tax collected by quarter."""

from datetime import date

from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from apps.core.decorators import owner_required

from . import nexus
from .models import Order


def _quarters(year):
    for quarter in range(4):
        start = date(year, quarter * 3 + 1, 1)
        end = date(year + 1, 1, 1) if quarter == 3 else date(year, quarter * 3 + 4, 1)
        yield f"{year} Q{quarter + 1}", start, end


@owner_required
def sales_by_state(request):
    today = timezone.localdate()
    tax_rows = []
    for label, start, end in _quarters(today.year):
        if start > today:
            break
        figures = Order.objects.filter(status__in=Order.PAID_STATUSES, ship_state="NY", paid_at__date__gte=start,
                                       paid_at__date__lt=end).aggregate(
            orders=Count("pk"), sales=Sum("total"), taxable=Sum("taxable_amount"), tax=Sum("tax_amount"))
        tax_rows.append((label, figures))
    return render(request, "checkout/owner/sales_by_state.html", {
        "rows": nexus.report(today), "tax_rows": tax_rows, "year": today.year,
    })
