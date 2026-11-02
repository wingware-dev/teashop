"""Back-office pages for checkout: sales by state against the nexus
thresholds, and New York sales tax collected by quarter, both net of
refunds."""

from django.shortcuts import render
from django.utils import timezone

from apps.core.decorators import owner_required

from . import nexus


@owner_required
def sales_by_state(request):
    today = timezone.localdate()
    return render(request, "checkout/owner/sales_by_state.html", {
        "rows": nexus.report(today), "tax_rows": nexus.ny_tax_by_quarter(today.year, today), "year": today.year,
    })
