"""Draft purchase orders from reorder levels, and stock counts.

Drafting never orders anything: a draft waits for the owner's approval
(inventory.services.approve_purchase_order), so nothing that costs money
happens without it.
"""

from dataclasses import dataclass, field

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit import agent_involved
from apps.inventory import services as inventory
from apps.inventory.models import Lot, PurchaseOrder, PurchaseOrderLine, StockMovement
from apps.inventory.reorder import reorders

from .models import StockCount, StockCountLine


@dataclass
class DraftResult:
    orders: list = field(default_factory=list)  # PurchaseOrders created or added to
    lines: list = field(default_factory=list)  # PurchaseOrderLines added
    no_supplier: list = field(default_factory=list)  # Reorders for items with no default supplier
    blends: list = field(default_factory=list)  # Reorders for blends made here: make a batch
    already_drafted: list = field(default_factory=list)  # Reorders already on a draft


def suggestions():
    """Reorders for active items that are low and need more than is on order."""
    return [r for r in reorders() if r.needs_order]


def last_unit_cost(item, supplier):
    line = (
        PurchaseOrderLine.objects.filter(item=item, order__supplier=supplier, unit_cost__isnull=False)
        .exclude(order__status=PurchaseOrder.Status.CANCELLED)
        .order_by("-order__created_at", "-pk")
        .first()
    )
    return line.unit_cost if line else None


def draft_purchase_orders():
    """Add a line for each suggested item to a draft purchase order for its
    default supplier, one draft per supplier (reusing a suggested draft
    still waiting for approval).  Items already on any draft are left as
    they are."""
    result = DraftResult()
    drafted = set(
        PurchaseOrderLine.objects.filter(order__status=PurchaseOrder.Status.DRAFT).values_list("item_id", flat=True)
    )
    by_supplier = {}
    for r in suggestions():
        if r.made_here:
            result.blends.append(r)
        elif r.item.pk in drafted:
            result.already_drafted.append(r)
        elif r.item.default_supplier is None:
            result.no_supplier.append(r)
        else:
            by_supplier.setdefault(r.item.default_supplier, []).append(r)
    today = timezone.localdate()
    with transaction.atomic():
        for supplier, wanted in by_supplier.items():
            order = (
                PurchaseOrder.objects.filter(
                    supplier=supplier, status=PurchaseOrder.Status.DRAFT, source=PurchaseOrder.Source.SUGGESTED
                )
                .order_by("-created_at")
                .first()
            )
            if order is None:
                order = PurchaseOrder.objects.create(
                    supplier=supplier,
                    source=PurchaseOrder.Source.SUGGESTED,
                    notes=f"Suggested from reorder levels on {today:%Y-%m-%d}.  Check quantities and prices, then approve.",
                )
            result.orders.append(order)
            for r in wanted:
                result.lines.append(
                    PurchaseOrderLine.objects.create(
                        order=order, item=r.item, quantity=r.suggested, unit_cost=last_unit_cost(r.item, supplier)
                    )
                )
    return result


def start_count(kinds=(), notes=""):
    """A new stock count of every lot with stock (recalled lots aside) of
    the given item kinds (default: all), expecting what the records say
    now."""
    lots = Lot.objects.filter(quantity_on_hand__gt=0).exclude(status=Lot.Status.RECALLED).select_related("item")
    if kinds:
        lots = lots.filter(item__kind__in=kinds)
    with transaction.atomic():
        count = StockCount.objects.create(kinds=list(kinds), notes=notes)
        StockCountLine.objects.bulk_create(
            [StockCountLine(count=count, lot=lot, expected=lot.quantity_on_hand) for lot in lots]
        )
    return count


def apply_count(count, user):
    """Turn each counted difference into a stock adjustment with its reason
    (count correction when there are more), and close the count.  All or
    nothing: on any problem no adjustment is made."""
    if agent_involved() or user is None or not user.is_authenticated:
        raise PermissionDenied("Only the owner can apply a stock count.")
    with transaction.atomic():
        count = StockCount.objects.select_for_update().get(pk=count.pk)
        if count.status != StockCount.Status.OPEN:
            raise ValidationError(f"{count} has already been applied.")
        errors = []
        lines = list(count.lines.select_related("lot__item"))
        for line in lines:
            try:
                line.full_clean()
            except ValidationError as error:
                errors += [f"{line.lot.code}: {m}" for m in error.messages]
        if errors:
            raise ValidationError(errors)
        movements = []
        for line in lines:
            if not line.difference:
                continue
            reason = line.reason or StockMovement.Reason.COUNT
            note = f"Stock count {count.pk}" + (f": {line.note}" if line.note else "")
            try:
                line.movement = inventory.adjust(line.lot, line.difference, reason, note[:300])
            except inventory.StockError as error:
                raise ValidationError(
                    f"{line.lot.code}: {' '.join(error.messages)}  (Stock was used since the count started; recount it.)"
                ) from error
            line.save(update_fields=["movement"])
            movements.append(line.movement)
        count.status = StockCount.Status.APPLIED
        count.applied_at = timezone.now()
        count.applied_by = user
        count.save()
    return movements
