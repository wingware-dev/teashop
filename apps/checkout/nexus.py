"""Sales per state against each state's economic-nexus threshold.

The shop collects sales tax only where it is registered
(settings.SALES_TAX_STATES).  Selling enough into another state obliges it
to register there too, so the dashboard warns when sales into a state
reach settings.NEXUS_ALERT_SHARE of its threshold, in the current or the
previous calendar year (the usual measuring period; a few states use the
last twelve months or other periods: check the state's rule when warned).

Sales here are what customers paid, without the sales tax collected, less
what was refunded.  A refund counts against the period it was issued in,
not the one the order was paid in (as New York's returns require), so an
order paid in one year and refunded in the next counts in full in the first
and comes off the second.  Refunds give back sales tax with them: a refund
is split between sales, taxable sales and tax in the proportions of its
order's total (refund_shares).
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from django.apps import apps
from django.conf import settings
from django.db.models import Count, F, Q, Sum
from django.utils import timezone

from .models import CENT, ZERO, NexusThreshold, Order
from .places import SHIPPING_STATES


def _year_range(year):
    tz = timezone.get_current_timezone()
    return datetime(year, 1, 1, tzinfo=tz), datetime(year + 1, 1, 1, tzinfo=tz)


# Orders that took payment: paid or shipped, or cancelled after payment (a
# cancellation refunds what was paid, and that refund comes off the period
# it was issued in, so the sale itself stays in the period it was paid in).
TOOK_PAYMENT = Q(status__in=Order.PAID_STATUSES) | Q(status=Order.Status.CANCELLED, paid_at__isnull=False)


@dataclass
class RefundShare:
    """What one refund takes off the sales figures: amount is the part of
    the order's total given back (at most the total: an overpayment refunded
    was never a sale), and taxable and tax its shares of the order's taxable
    amount and the sales tax collected."""
    refund: object
    state: str
    amount: Decimal
    taxable: Decimal
    tax: Decimal


def _part(value, numerator, denominator):
    if not denominator:
        return ZERO
    return (value * numerator / denominator).quantize(CENT, rounding=ROUND_HALF_UP)


def refund_shares(**refund_filters):
    """A RefundShare for each refund matching refund_filters (on
    fulfillment's Refund, e.g. created_at__gte=...), oldest first.

    The tax given back with a partial refund is its share of the order's
    total, worked out on the order's refunds to date so that, however an
    order is refunded, its refunds' tax adds up to exactly the tax collected
    once all of it is refunded."""
    Refund = apps.get_model("fulfillment", "Refund")
    wanted = list(Refund.objects.filter(**refund_filters).select_related("order").order_by("created_at", "pk"))
    if not wanted:
        return []
    history = defaultdict(list)
    for refund in (Refund.objects.filter(order__in={r.order_id for r in wanted})
                   .only("pk", "order_id", "amount", "created_at").order_by("created_at", "pk")):
        history[refund.order_id].append(refund)
    shares = []
    for refund in wanted:
        order = refund.order
        before = ZERO
        for earlier in history[order.pk]:
            if earlier.pk == refund.pk:
                break
            before += earlier.amount
        upto = min(before + refund.amount, order.total)
        before = min(before, order.total)
        shares.append(RefundShare(
            refund, order.ship_state, upto - before,
            _part(upto, order.taxable_amount, order.total) - _part(before, order.taxable_amount, order.total),
            _part(upto, order.tax_amount, order.total) - _part(before, order.tax_amount, order.total)))
    return shares


def sales_by_state(year):
    """{state: (sales, orders)} for year: sales paid in it less refunds
    issued in it, without sales tax; orders paid in it and not cancelled."""
    start, end = _year_range(year)
    rows = (Order.objects.filter(TOOK_PAYMENT, paid_at__gte=start, paid_at__lt=end)
            .values("ship_state").annotate(
                sales=Sum(F("total") - F("tax_amount")),
                orders=Count("pk", filter=Q(status__in=Order.PAID_STATUSES))))
    sales = defaultdict(lambda: ZERO)
    orders = defaultdict(int)
    for row in rows:
        sales[row["ship_state"]] += row["sales"] or ZERO
        orders[row["ship_state"]] += row["orders"]
    for share in refund_shares(created_at__gte=start, created_at__lt=end):
        sales[share.state] -= share.amount - share.tax
    return {state: (sales[state], orders[state]) for state in sales}


def ny_tax_by_quarter(year, today=None):
    """[(label, figures)] for each quarter of year begun by today: New York
    orders paid in the quarter, and their sales (with tax), taxable amount
    and tax collected, less the refunds issued in the quarter."""
    today = today or timezone.localdate()
    rows = []
    for quarter in range(4):
        start = date(year, quarter * 3 + 1, 1)
        end = date(year + 1, 1, 1) if quarter == 3 else date(year, quarter * 3 + 4, 1)
        if start > today:
            break
        figures = Order.objects.filter(TOOK_PAYMENT, ship_state="NY", paid_at__date__gte=start,
                                       paid_at__date__lt=end).aggregate(
            orders=Count("pk"), sales=Sum("total"), taxable=Sum("taxable_amount"), tax=Sum("tax_amount"))
        figures = {"orders": figures["orders"], "sales": figures["sales"] or ZERO,
                   "taxable": figures["taxable"] or ZERO, "tax": figures["tax"] or ZERO,
                   "refunds": 0, "refunded": ZERO}
        for share in refund_shares(order__ship_state="NY", created_at__date__gte=start, created_at__date__lt=end):
            figures["refunds"] += 1
            figures["refunded"] += share.amount
            figures["sales"] -= share.amount
            figures["taxable"] -= share.taxable
            figures["tax"] -= share.tax
        rows.append((f"{year} Q{quarter + 1}", figures))
    return rows


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
