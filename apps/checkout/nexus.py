"""Sales per state against each state's economic-nexus threshold.

The shop collects sales tax only where it is registered
(settings.SALES_TAX_STATES).  Selling enough into another state obliges it
to register there too, so the dashboard warns when sales into a state
reach settings.NEXUS_ALERT_SHARE of its threshold, in the current or the
previous calendar year (the usual measuring period; a few states use the
last twelve months or other periods: check the state's rule when warned).

Sales here are what customers paid, without the sales tax collected.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, F, Sum
from django.utils import timezone

from .models import ZERO, NexusThreshold, Order
from .places import SHIPPING_STATES


def _year_range(year):
    tz = timezone.get_current_timezone()
    return datetime(year, 1, 1, tzinfo=tz), datetime(year + 1, 1, 1, tzinfo=tz)


def sales_by_state(year):
    """{state: (sales, orders)} for orders paid in year."""
    start, end = _year_range(year)
    rows = (Order.objects.filter(status__in=Order.PAID_STATUSES, paid_at__gte=start, paid_at__lt=end)
            .values("ship_state").annotate(sales=Sum(F("total") - F("tax_amount")), orders=Count("pk")))
    return {row["ship_state"]: (row["sales"] or ZERO, row["orders"]) for row in rows}


def share_of(threshold, sales, orders):
    """How far towards the threshold (1.0 = reached), or None if the state
    has no sales tax or no threshold."""
    if threshold is None or not threshold.has_sales_tax:
        return None
    parts = []
    if threshold.sales:
        parts.append(Decimal(sales) / threshold.sales)
    if threshold.transactions:
        parts.append(Decimal(orders) / threshold.transactions)
    if not parts:
        return None
    return float(min(parts) if threshold.needs_both else max(parts))


@dataclass
class StateRow:
    state: str
    name: str
    sales: Decimal
    orders: int
    last_sales: Decimal
    last_orders: int
    threshold: NexusThreshold
    share: float
    collecting: bool

    @property
    def percent(self):
        return None if self.share is None else round(self.share * 100)

    @property
    def status(self):
        if self.collecting:
            return "Collecting sales tax"
        if self.threshold is not None and not self.threshold.has_sales_tax:
            return "No state sales tax"
        if self.share is None:
            return "No threshold entered"
        if self.share >= 1:
            return "Threshold passed: register to collect"
        if self.share >= settings.NEXUS_ALERT_SHARE:
            return "Nearing the threshold"
        return ""

    @property
    def needs_action(self):
        return not self.collecting and self.share is not None and self.share >= settings.NEXUS_ALERT_SHARE


def report(today=None):
    """A StateRow for every state with sales this year or last, plus the
    states the shop collects in."""
    today = today or timezone.localdate()
    this_year, last_year = sales_by_state(today.year), sales_by_state(today.year - 1)
    thresholds = {t.state: t for t in NexusThreshold.objects.all()}
    names = dict(SHIPPING_STATES)
    rows = []
    for state in sorted(set(this_year) | set(last_year) | set(settings.SALES_TAX_STATES)):
        if state not in names:
            continue
        sales, orders = this_year.get(state, (ZERO, 0))
        last_sales, last_orders = last_year.get(state, (ZERO, 0))
        threshold = thresholds.get(state)
        shares = [s for s in (share_of(threshold, sales, orders), share_of(threshold, last_sales, last_orders))
                  if s is not None]
        rows.append(StateRow(state, names[state], sales, orders, last_sales, last_orders, threshold,
                             max(shares) if shares else None, state in settings.SALES_TAX_STATES))
    return rows
