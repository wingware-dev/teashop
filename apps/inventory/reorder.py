"""Reorder levels and suggested order quantities, from how fast each item
is used and how long the supplier takes to deliver.

    daily use     = stock used in the last REORDER_USAGE_WINDOW_DAYS days / days
    reorder level = daily use × (lead time + safety days), never below the
                    item's own reorder level
    suggested     = daily use × (lead time + safety days + cover days)
                    - (usable stock + still on order), rounded up to the
                    item's minimum order

"Used" means packed for orders, used in blend batches, and given away as
samples or marketing, less stock returned (a cancelled order unpacked);
losses are left out, since they are not demand.
An item first received within the window is measured over the days since
then (at least REORDER_MIN_HISTORY_DAYS), so a new tea isn't
underestimated.  Blends made here have no supplier: their lead time is
BLEND_LEAD_DAYS, and the suggestion is a blend batch, not an order.
"""

import math
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import ROUND_CEILING, Decimal

from django.conf import settings
from django.db.models import Min, Q, Sum
from django.utils import timezone

from .models import Item, Lot, PurchaseOrder, PurchaseOrderLine, Recipe, StockMovement


@dataclass
class Reorder:
    item: Item
    daily_use: Decimal
    lead_days: int
    safety_days: int
    cover_days: int
    level: int
    on_hand: int
    on_order: int
    suggested: int
    made_here: bool

    @property
    def is_low(self):
        return self.level > 0 and self.on_hand <= self.level

    @property
    def needs_order(self):
        return self.is_low and self.suggested > 0

    def text(self, name):
        return self.item.format_quantity(getattr(self, name))

    @property
    def display(self):
        """Quantities formatted with their unit, for templates."""
        daily = self.daily_use.quantize(Decimal("0.1")) if self.daily_use else 0
        return {
            "daily_use": f"{daily} g" if self.item.by_weight else f"{daily}",
            "level": self.text("level"),
            "on_hand": self.text("on_hand"),
            "on_order": self.text("on_order") if self.on_order else "—",
            "suggested": self.text("suggested") if self.needs_order else "—",
        }

    @property
    def days_left(self):
        """Days the usable stock lasts at the current rate, or None."""
        if not self.daily_use:
            return None
        return int(self.on_hand / self.daily_use)


def used_movements():
    """Movements that make up use: demand going out (negative) and stock
    returned from it (positive 'returned' adjustments, as from
    catalog.services.reverse_package), so their sum is minus the net use."""
    demand = Q(kind__in=[StockMovement.Kind.SALE, StockMovement.Kind.BLEND_INPUT]) | Q(
        kind=StockMovement.Kind.ADJUSTMENT, reason__in=list(StockMovement.MARKETING_REASONS)
    )
    returned = Q(kind=StockMovement.Kind.ADJUSTMENT, reason=StockMovement.Reason.RETURNED, quantity__gt=0)
    return StockMovement.objects.filter((demand & Q(quantity__lt=0)) | returned)


def daily_use_by_item(items, today=None):
    """{item_id: Decimal grams or pieces per day}."""
    today = today or timezone.localdate()
    window = settings.REORDER_USAGE_WINDOW_DAYS
    since = today - timedelta(days=window)
    start = timezone.make_aware(datetime.combine(since, time.min))
    ids = [item.pk for item in items]
    used = dict(
        used_movements()
        .filter(lot__item_id__in=ids, created_at__gte=start)
        .values_list("lot__item_id")
        .annotate(total=Sum("quantity"))
        .values_list("lot__item_id", "total")
    )
    first = dict(
        Lot.objects.filter(item_id__in=ids).values_list("item_id").annotate(first=Min("received_on")).values_list("item_id", "first")
    )
    rates = {}
    for item_id in ids:
        # A return in the window for a sale before it can outweigh the
        # window's use: never below nothing.
        total = max(-(used.get(item_id) or 0), 0)
        if not total:
            rates[item_id] = Decimal(0)
            continue
        days = window
        if first.get(item_id) and first[item_id] > since:
            days = max((today - first[item_id]).days, settings.REORDER_MIN_HISTORY_DAYS)
        rates[item_id] = Decimal(total) / Decimal(days)
    return rates


def on_order_by_item(items):
    """{item_id: quantity still to come on approved, open purchase orders}."""
    result = {}
    lines = PurchaseOrderLine.objects.filter(item__in=items, order__status__in=PurchaseOrder.OPEN).annotate(
        received=Sum("lots__quantity_received", default=0)
    )
    for line in lines:
        result[line.item_id] = result.get(line.item_id, 0) + max(line.quantity - line.received, 0)
    return result


def lead_days(item, made_here):
    if made_here:
        return settings.BLEND_LEAD_DAYS
    supplier = item.default_supplier
    if supplier and supplier.lead_time_days is not None:
        return supplier.lead_time_days
    return settings.REORDER_DEFAULT_LEAD_DAYS


def round_up(quantity, multiple):
    if quantity <= 0:
        return 0
    if multiple and multiple > 1:
        return math.ceil(quantity / multiple) * multiple
    return int(quantity)


def reorders(items=None, today=None):
    """[Reorder] for the given items (default: every active item)."""
    if items is None:
        items = Item.objects.filter(is_active=True)
    items = list(items.select_related("default_supplier"))
    ids = [item.pk for item in items]
    usable = dict(
        Lot.objects.usable()
        .filter(item_id__in=ids)
        .values_list("item_id")
        .annotate(total=Sum("quantity_on_hand"))
        .values_list("item_id", "total")
    )
    blends = set(Recipe.objects.filter(is_active=True, output_item_id__in=ids).values_list("output_item_id", flat=True))
    rates = daily_use_by_item(items, today)
    on_order = on_order_by_item(items)
    results = []
    for item in items:
        item.usable_on_hand = usable.get(item.pk, 0)
        made_here = item.pk in blends
        rate = rates.get(item.pk, Decimal(0)) if item.auto_reorder else Decimal(0)
        lead = lead_days(item, made_here)
        safety = item.safety_days if item.safety_days is not None else settings.REORDER_SAFETY_DAYS
        cover = item.cover_days if item.cover_days is not None else settings.REORDER_COVER_DAYS
        computed = int((rate * (lead + safety)).to_integral_value(ROUND_CEILING))
        level = max(item.reorder_level, computed)
        coming = on_order.get(item.pk, 0)
        if rate:
            target = int((rate * (lead + safety + cover)).to_integral_value(ROUND_CEILING))
        else:
            # No history: bring stock back to twice the fixed reorder level.
            target = 2 * item.reorder_level
        suggested = round_up(target - item.usable_on_hand - coming, item.minimum_order)
        if suggested and item.minimum_order:
            suggested = max(suggested, item.minimum_order)
        results.append(
            Reorder(
                item=item,
                daily_use=rate,
                lead_days=lead,
                safety_days=safety,
                cover_days=cover,
                level=level,
                on_hand=item.usable_on_hand,
                on_order=coming,
                suggested=suggested,
                made_here=made_here,
            )
        )
    return results


def reorder_level(item):
    return reorders(Item.objects.filter(pk=item.pk))[0].level
