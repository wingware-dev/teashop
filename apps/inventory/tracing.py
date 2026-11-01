"""Lot traceability, for recalls: from a supplier lot forward to the blend
lots made with it and the customer orders packed from any of them, and
from a blend lot back to its ingredient lots."""

from dataclasses import dataclass, field

from django.db import transaction

from .models import BlendInput, Lot, StockMovement


@dataclass
class OrderShipment:
    reference: str
    lot: Lot
    quantity: int
    packed_at: object


@dataclass
class Trace:
    lot: Lot
    sources: list = field(default_factory=list)
    derived: list = field(default_factory=list)
    orders: list = field(default_factory=list)

    def order_references(self):
        return sorted({o.reference for o in self.orders if o.reference})


def source_lots(lot):
    """The ingredient lots a blend lot was made from, all the way down."""
    found, queue, seen = [], [lot], {lot.pk}
    while queue:
        current = queue.pop(0)
        inputs = BlendInput.objects.filter(batch__output_lot=current).select_related("lot__item")
        for blend_input in inputs:
            if blend_input.lot_id not in seen:
                seen.add(blend_input.lot_id)
                found.append(blend_input.lot)
                queue.append(blend_input.lot)
    return found


def derived_lots(lot):
    """The blend lots made using lot, and blends made from those."""
    found, queue, seen = [], [lot], {lot.pk}
    while queue:
        current = queue.pop(0)
        outputs = (
            Lot.objects.filter(blend_batch__inputs__lot=current).select_related("item").distinct()
        )
        for output in outputs:
            if output.pk not in seen:
                seen.add(output.pk)
                found.append(output)
                queue.append(output)
    return found


def trace(lot):
    derived = derived_lots(lot)
    sales = (
        StockMovement.objects.filter(lot__in=[lot, *derived], kind=StockMovement.Kind.SALE)
        .select_related("lot__item")
        .order_by("created_at", "pk")
    )
    orders = [OrderShipment(m.reference, m.lot, -m.quantity, m.created_at) for m in sales]
    return Trace(lot=lot, sources=source_lots(lot), derived=derived, orders=orders)


def recall(lot, note=""):
    """Mark lot and every blend lot made from it as recalled, so nothing
    more is packed from them.  Returns the trace, whose orders are the
    customers to contact."""
    result = trace(lot)
    with transaction.atomic():
        for target in [lot, *result.derived]:
            if target.status != Lot.Status.RECALLED:
                target.status = Lot.Status.RECALLED
                target.status_note = note or (f"Recalled with lot {lot.code}" if target is not lot else "Recalled")
                target.save(update_fields=["status", "status_note"])
    return result
