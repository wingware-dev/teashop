"""Sales by period, product, category and channel; cost of goods sold,
gross margin, stock value and loss.

Sales count when the order was paid, refunds when they were issued (as the
sales-tax returns want), and cost of goods when the package was packed.
Money is without sales tax unless a figure says it is the tax.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.checkout.models import Order, OrderLine
from apps.checkout.nexus import TOOK_PAYMENT, refund_shares
from apps.purchasing import reports as purchasing

ZERO = Decimal("0.00")
money = purchasing.money
aware = purchasing.aware

GROUPINGS = {"day": "Day", "week": "Week", "month": "Month", "quarter": "Quarter", "year": "Year"}
SHOP, SUBSCRIPTIONS = "Shop", "Subscriptions"


def period_start(day, by):
    if by == "day":
        return day
    if by == "week":
        return day - timedelta(days=day.weekday())
    if by == "month":
        return day.replace(day=1)
    if by == "quarter":
        return date(day.year, (day.month - 1) // 3 * 3 + 1, 1)
    return date(day.year, 1, 1)


def next_period(start, by):
    if by == "day":
        return start + timedelta(days=1)
    if by == "week":
        return start + timedelta(days=7)
    if by == "month":
        return purchasing.add_months(start, 1)
    if by == "quarter":
        return purchasing.add_months(start, 3)
    return date(start.year + 1, 1, 1)


def period_label(start, by):
    if by == "day":
        return f"{start:%a %b %-d, %Y}"
    if by == "week":
        return f"Week of {start:%b %-d, %Y}"
    if by == "month":
        return f"{start:%B %Y}"
    if by == "quarter":
        return f"{start.year} Q{(start.month - 1) // 3 + 1}"
    return str(start.year)


def channel_of(order):
    return SUBSCRIPTIONS if order.subscription_id else SHOP


@dataclass
class SalesRow:
    label: str
    start: date | None = None
    orders: int = 0
    units: int = 0
    gross: Decimal = ZERO  # items at their prices
    discounts: Decimal = ZERO
    shipping: Decimal = ZERO  # shipping charged
    tax: Decimal = ZERO  # sales tax collected (not part of the sales)
    refunds: Decimal = ZERO  # given back, without its sales tax
    refunded_tax: Decimal = ZERO
    _orders: set = field(default_factory=set, repr=False)

    @property
    def items(self):
        return self.gross - self.discounts

    @property
    def net(self):
        """Net sales: items after discounts, plus shipping, less refunds."""
        return self.items + self.shipping - self.refunds

    def add_line(self, line):
        self.units += line.quantity
        self.gross += line.line_total
        self.discounts += line.discount_share
        if line.order_id not in self._orders:
            self._orders.add(line.order_id)
            self.orders += 1


def _lines(start, end):
    return (OrderLine.objects.filter(order__in=Order.objects.filter(TOOK_PAYMENT, paid_at__gte=aware(start),
                                                                      paid_at__lt=aware(end)))
            .select_related("order", "size_option__product__category"))


def _orders(start, end):
    return Order.objects.filter(TOOK_PAYMENT, paid_at__gte=aware(start), paid_at__lt=aware(end))


def _refunds(start, end):
    return refund_shares(created_at__gte=aware(start), created_at__lt=aware(end))


def by_period(start, end, by="month"):
    """[SalesRow] for each period from start up to end, oldest first, and
    the total row."""
    rows = {}
    first = period_start(start, by)
    cursor = first
    while cursor < end:
        rows[cursor] = SalesRow(period_label(cursor, by), cursor)
        cursor = next_period(cursor, by)

    def row_for(moment):
        return rows[period_start(timezone.localtime(moment).date(), by)]

    for line in _lines(start, end):
        row_for(line.order.paid_at).add_line(line)
    for order in _orders(start, end):
        row = row_for(order.paid_at)
        row.shipping += order.shipping_amount
        row.tax += order.tax_amount
    for share in _refunds(start, end):
        row = row_for(share.refund.created_at)
        row.refunds += share.amount - share.tax
        row.refunded_tax += share.tax
    ordered = [rows[key] for key in sorted(rows)]
    return ordered, total_of(ordered)


def total_of(rows, label="Total"):
    total = SalesRow(label)
    for row in rows:
        for name in ("orders", "units", "gross", "discounts", "shipping", "tax", "refunds", "refunded_tax"):
            setattr(total, name, getattr(total, name) + getattr(row, name))
    return total


def _grouped(start, end, key):
    rows = {}
    for line in _lines(start, end):
        label = key(line)
        rows.setdefault(label, SalesRow(label)).add_line(line)
    return sorted(rows.values(), key=lambda r: (-r.items, r.label))


def by_product(start, end):
    """[SalesRow] per product (and subscription plan), biggest first.
    Shipping and refunds are not split by product."""
    return _grouped(start, end, lambda line: line.product_name)


def category_of(line):
    if line.kind == OrderLine.Kind.SUBSCRIPTION:
        return SUBSCRIPTIONS
    product = line.size_option.product if line.size_option_id else None
    if product is not None and product.category_id:
        return product.category.name
    return "Teas, no category" if line.kind == OrderLine.Kind.TEA else "Merchandise, no category"


def by_category(start, end):
    return _grouped(start, end, category_of)


def by_channel(start, end):
    """[SalesRow] per channel: the shop's own checkout, subscription
    deliveries.  Here shipping and refunds are split too."""
    rows = {}
    for line in _lines(start, end):
        label = channel_of(line.order)
        rows.setdefault(label, SalesRow(label)).add_line(line)
    for order in _orders(start, end):
        row = rows.setdefault(channel_of(order), SalesRow(channel_of(order)))
        row.shipping += order.shipping_amount
        row.tax += order.tax_amount
    for share in _refunds(start, end):
        label = channel_of(share.refund.order)
        row = rows.setdefault(label, SalesRow(label))
        row.refunds += share.amount - share.tax
        row.refunded_tax += share.tax
    return sorted(rows.values(), key=lambda r: (-r.net, r.label))


@dataclass
class Margin:
    net_sales: Decimal
    goods_cost: Decimal  # cost of goods sold: landed cost of what was packed
    tariffs: Decimal
    uncosted: int  # packages with no landed cost (their cost counts as 0)
    postage: Decimal
    fees: Decimal
    fees_estimated: bool
    loss: Decimal  # stock spoiled, damaged, missing, at landed cost
    samples: Decimal  # given away as samples and marketing
    stock_value: Decimal
    uncosted_lots: int

    @property
    def gross_margin(self):
        return self.net_sales - self.goods_cost

    @property
    def gross_margin_percent(self):
        return None if not self.net_sales else (self.gross_margin * 100 / self.net_sales).quantize(Decimal("0.1"))

    @property
    def after_fulfilment(self):
        """Gross margin less the postage bought and payment fees."""
        return self.gross_margin - self.postage - self.fees


def loss_cost(start, end):
    """Landed cost of stock lost (spoiled, damaged, missing, counted short)
    from start up to end."""
    total = ZERO
    for movement in purchasing.adjustments(start, end).filter(reason__in=purchasing.LOSS_REASONS):
        total += purchasing.movement_cost(movement) or ZERO
    return money(total)


def fees_and_postage(start, end):
    """(postage, fees, any fee estimated) for orders paid from start to end."""
    orders = list(_orders(start, end))
    postage = sum(purchasing.postage_paid(orders).values(), ZERO) if orders else ZERO
    fees, estimated = ZERO, False
    for order in orders:
        fee, guess = purchasing.payment_fee(order)
        fees += fee
        estimated = estimated or guess
    return money(postage), money(fees), estimated


def margin(start, end):
    _rows, total = by_period(start, end, "year")
    _by_tea, _by_size, packed = purchasing.profitability(start, end)
    postage, fees, estimated = fees_and_postage(start, end)
    value, uncosted_lots = purchasing.stock_value()
    return Margin(
        net_sales=total.net, goods_cost=packed.cost, tariffs=packed.tariffs, uncosted=packed.uncosted,
        postage=postage, fees=fees, fees_estimated=estimated, loss=loss_cost(start, end),
        samples=money(purchasing.marketing_cost(start, end)), stock_value=value, uncosted_lots=uncosted_lots)


def refunds_total(start, end):
    """(amount without tax, tax) refunded from start up to end."""
    amount = tax = ZERO
    for share in _refunds(start, end):
        amount += share.amount - share.tax
        tax += share.tax
    return amount, tax


def sales_tax_collected(start, end):
    return _orders(start, end).aggregate(tax=Sum("tax_amount"))["tax"] or ZERO
