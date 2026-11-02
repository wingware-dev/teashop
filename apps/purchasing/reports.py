"""Loss trends and profitability, valued at each lot's landed cost
(purchase price, shipping, tariffs and duties)."""

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal

from django.utils import timezone

from apps.catalog.models import SoldPackage
from apps.inventory.models import Item, Lot, StockMovement

R = StockMovement.Reason
# Grouping of adjustment reasons in the reports.  Samples and giveaways
# are marketing expense, personal use is the owner's, the rest is loss.
LOSS_REASONS = [R.SPOILED, R.DAMAGED, R.UNKNOWN, R.OTHER, R.COUNT]
MARKETING_REASONS = list(StockMovement.MARKETING_REASONS)
PERSONAL_REASONS = [R.PERSONAL]
ZERO = Decimal("0.00")


def money(value):
    return (value or ZERO).quantize(Decimal("0.01"))


def month_start(day):
    return day.replace(day=1)


def add_months(day, months):
    month = day.month - 1 + months
    return date(day.year + month // 12, month % 12 + 1, 1)


def aware(day):
    return timezone.make_aware(datetime.combine(day, time.min))


@dataclass
class MonthRow:
    month: date
    by_reason: dict = field(default_factory=dict)  # reason -> cost
    loss: Decimal = ZERO
    marketing: Decimal = ZERO
    personal: Decimal = ZERO
    uncosted: int = 0  # adjustments from lots with no landed cost


@dataclass
class ItemLoss:
    item: Item
    quantity: int = 0
    cost: Decimal = ZERO


def movement_cost(movement):
    """What a movement took out of stock, at its lot's landed cost (positive
    for stock removed), or None if the lot has no cost."""
    unit = movement.lot.unit_cost()
    return None if unit is None else money(-movement.quantity * unit)


def adjustments(start, end):
    return (
        StockMovement.objects.filter(kind=StockMovement.Kind.ADJUSTMENT, created_at__gte=aware(start), created_at__lt=aware(end))
        .exclude(reason=R.RETURNED)
        .select_related("lot__item")
    )


def loss_trend(months=12, today=None):
    """[MonthRow] for the last `months` months, oldest first, and the items
    with the most loss over them, [ItemLoss]."""
    today = today or timezone.localdate()
    first = add_months(month_start(today), -(months - 1))
    end = add_months(month_start(today), 1)
    rows = OrderedDict((add_months(first, n), MonthRow(add_months(first, n))) for n in range(months))
    items = {}
    for movement in adjustments(first, end):
        row = rows[month_start(timezone.localtime(movement.created_at).date())]
        cost = movement_cost(movement)
        if cost is None:
            row.uncosted += 1
            cost = ZERO
        row.by_reason[movement.reason] = row.by_reason.get(movement.reason, ZERO) + cost
        if movement.reason in MARKETING_REASONS:
            row.marketing += cost
        elif movement.reason in PERSONAL_REASONS:
            row.personal += cost
        else:
            row.loss += cost
            loss = items.setdefault(movement.lot.item_id, ItemLoss(movement.lot.item))
            loss.quantity += -movement.quantity
            loss.cost += cost
    worst = sorted((i for i in items.values() if i.cost > 0 or i.quantity > 0), key=lambda i: (-i.cost, -i.quantity))
    return list(rows.values()), worst[:10]


@dataclass
class ProfitRow:
    label: str
    packages: int = 0
    grams: int = 0
    revenue: Decimal = ZERO
    tea_cost: Decimal = ZERO
    tariffs: Decimal = ZERO
    packaging_cost: Decimal = ZERO
    uncosted: int = 0  # packages whose tea or packaging had no landed cost

    @property
    def cost(self):
        return self.tea_cost + self.packaging_cost

    @property
    def margin(self):
        return self.revenue - self.cost

    @property
    def margin_percent(self):
        return None if not self.revenue else (self.margin * 100 / self.revenue).quantize(Decimal("0.1"))


def average_unit_costs():
    """{item_id: average landed cost per gram or piece} over all its lots
    with a cost, weighted by quantity received (for packaging, whose
    pieces aren't traced to one package)."""
    totals = {}
    for lot in Lot.objects.filter(landed_cost__isnull=False).select_related("item"):
        cost, quantity = totals.get(lot.item_id, (ZERO, 0))
        totals[lot.item_id] = (cost + lot.unit_cost() * lot.quantity_received, quantity + lot.quantity_received)
    return {item_id: cost / quantity for item_id, (cost, quantity) in totals.items() if quantity}


def package_costs(package, average):
    """(tea cost, tariffs, packaging cost, complete) for one package.  The
    tea is valued at its own lot's landed cost; packaging and merchandise
    at their average landed cost."""
    tea = tariffs = packaging = Decimal(0)
    complete = True
    if package.tea_lot_id:
        unit = package.tea_lot.unit_cost()
        tariff = package.tea_lot.unit_tariff()
        if unit is None:
            complete = False
        else:
            tea = unit * package.tea_grams
        if tariff is not None:
            tariffs = tariff * package.tea_grams
    for line in package.size_option.bom_lines.all():
        unit = average.get(line.item_id)
        if unit is None:
            complete = False
        else:
            packaging += unit * line.quantity
    return tea, tariffs, packaging, complete


def profitability(start, end):
    """Revenue, landed cost and margin of packages packed from start up to
    (not including) end, per tea (or merchandise item) and per size, with
    the total.  Returns (by_tea, by_size, total), each row a ProfitRow."""
    average = average_unit_costs()
    packages = (
        SoldPackage.objects.filter(packed_at__gte=aware(start), packed_at__lt=aware(end), reversed_at=None)
        .select_related("size_option__product__tea", "tea_lot__item")
        .prefetch_related("size_option__bom_lines")
    )
    by_tea, by_size = {}, {}
    total = ProfitRow("Total")
    for package in packages:
        size = package.size_option
        product = size.product
        tea_label = product.tea.name if product.tea_id else product.name
        tea, tariffs, packaging, complete = package_costs(package, average)
        for row in (by_tea.setdefault(tea_label, ProfitRow(tea_label)), by_size.setdefault(size.pk, ProfitRow(f"{size} ({size.sku})")), total):
            row.packages += 1
            row.grams += package.tea_grams or 0
            row.revenue += package.amount
            row.tea_cost += tea
            row.tariffs += tariffs
            row.packaging_cost += packaging
            row.uncosted += 0 if complete else 1
    for row in [*by_tea.values(), *by_size.values(), total]:
        row.tea_cost, row.tariffs, row.packaging_cost = money(row.tea_cost), money(row.tariffs), money(row.packaging_cost)
    order = lambda rows: sorted(rows, key=lambda r: (-r.margin, r.label))  # noqa: E731
    return order(by_tea.values()), order(by_size.values()), total


def marketing_cost(start, end):
    """Landed cost of stock given away as samples and marketing."""
    total = ZERO
    for movement in adjustments(start, end).filter(reason__in=MARKETING_REASONS):
        total += movement_cost(movement) or ZERO
    return total


def stock_value():
    """Landed cost of usable stock now, and how many lots have no cost."""
    value, uncosted = ZERO, 0
    for lot in Lot.objects.usable().select_related("item"):
        unit = lot.unit_cost()
        if unit is None:
            uncosted += 1
        else:
            value += unit * lot.quantity_on_hand
    return money(value), uncosted
