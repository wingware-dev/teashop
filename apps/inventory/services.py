"""Changing stock.  Everything that moves stock goes through here, so a
lot's quantity on hand always equals the sum of its movements and never
goes below zero.

- post_movement(): one change to one lot (the building block).
- adjust(): a stock adjustment with a reason (count, spoiled, sample...).
- consume(): take a quantity of an item for an order, oldest best-by first.
- pick_lot(): the lot to pack one package of tea from.
- make_blend(): run a recipe, using ingredient lots and making a blend lot.
"""

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit import agent_involved

from .models import BlendBatch, BlendInput, Item, Lot, PurchaseOrder, StockMovement


class StockError(ValidationError):
    """Not enough usable stock, or a lot that cannot be used.  A
    ValidationError, so forms show it to the owner as an error."""


def post_movement(lot, quantity, kind, *, reason="", reference="", note="", blend_batch=None):
    """Add quantity (negative to remove) to lot, recording the movement.

    Stock can only be taken from an active lot, except by an adjustment
    (writing off a recalled lot, say).  Returns the StockMovement.
    """
    if not quantity:
        raise ValueError("A stock movement needs a non-zero quantity")
    if kind == StockMovement.Kind.ADJUSTMENT and not reason:
        raise ValueError("A stock adjustment needs a reason")
    with transaction.atomic():
        locked = Lot.objects.select_for_update().select_related("item").get(pk=lot.pk)
        if quantity < 0 and kind != StockMovement.Kind.ADJUSTMENT and locked.status != Lot.Status.ACTIVE:
            raise StockError(f"Lot {locked.code} is {locked.get_status_display().lower()} and cannot be used.")
        new_total = locked.quantity_on_hand + quantity
        if new_total < 0:
            raise StockError(
                f"Lot {locked.code} has only {locked.format_quantity(locked.quantity_on_hand)}, "
                f"not {locked.format_quantity(-quantity)}."
            )
        Lot.objects.filter(pk=locked.pk).update(quantity_on_hand=new_total)
        lot.quantity_on_hand = new_total
        return StockMovement.objects.create(
            lot=locked,
            kind=kind,
            quantity=quantity,
            reason=reason,
            reference=reference,
            note=note,
            blend_batch=blend_batch,
        )


def adjust(lot, quantity, reason, note=""):
    """A stock adjustment: a count correction, a loss, or stock used for
    marketing (samples, giveaways)."""
    if reason not in StockMovement.Reason.values:
        raise ValueError(f"Unknown adjustment reason {reason!r}")
    return post_movement(lot, quantity, StockMovement.Kind.ADJUSTMENT, reason=reason, note=note)


def consume(item, quantity, *, reference="", note="", kind=StockMovement.Kind.SALE):
    """Take quantity of item from its usable lots, oldest best-by first,
    spreading over as many lots as needed.  Returns the movements.

    For pieces (tins, labels, boxes), where which lot they come from does
    not matter much.  A package of tea comes from one lot: see pick_lot().
    """
    if quantity <= 0:
        raise ValueError("Quantity to consume must be positive")
    with transaction.atomic():
        lots = list(item.usable_lots().select_for_update())
        available = sum(lot.quantity_on_hand for lot in lots)
        if available < quantity:
            raise StockError(
                f"Not enough {item}: {item.format_quantity(available)} usable, {item.format_quantity(quantity)} needed."
            )
        movements = []
        remaining = quantity
        for lot in lots:
            take = min(lot.quantity_on_hand, remaining)
            if take:
                movements.append(post_movement(lot, -take, kind, reference=reference, note=note))
                remaining -= take
            if not remaining:
                break
        return movements


def pick_lot(item, quantity, lots=None):
    """The lot to pack quantity of item from: the usable lot with the
    earliest best-by date that holds at least that much.  A package must
    come from a single lot, so its label names one lot code; a remnant too
    small for a package is left for an adjustment or a smaller size.

    lots narrows the choice (e.g. organic lots only); it defaults to
    item.usable_lots(), and must keep its oldest-first order."""
    for lot in item.usable_lots() if lots is None else lots:
        if lot.quantity_on_hand >= quantity:
            return lot
    raise StockError(f"No single usable lot of {item} holds {item.format_quantity(quantity)}.")


def approve_purchase_order(order, user):
    """The owner approves a draft purchase order: it becomes ordered, with
    who approved it and when.  Nothing else can move a draft on, so no
    order (and no spending) happens without this.  AI agents can draft
    orders but never approve them."""
    if agent_involved():
        raise PermissionDenied("AI agents cannot approve purchase orders.")
    if user is None or not user.is_authenticated or not user.is_staff:
        raise PermissionDenied("Only the owner can approve purchase orders.")
    with transaction.atomic():
        order = PurchaseOrder.objects.select_for_update().get(pk=order.pk)
        if order.status != PurchaseOrder.Status.DRAFT:
            raise ValidationError(f"{order} is {order.get_status_display().lower()}, not a draft.")
        if not order.lines.exists():
            raise ValidationError(f"{order} has no lines.")
        today = timezone.localdate()
        order.status = PurchaseOrder.Status.ORDERED
        order.approved_by = user
        order.approved_at = timezone.now()
        order.ordered_on = order.ordered_on or today
        if not order.expected_on and order.supplier.lead_time_days is not None:
            order.expected_on = order.ordered_on + timedelta(days=order.supplier.lead_time_days)
        order.save()
    return order


def cancel_purchase_order(order):
    if order.status in (PurchaseOrder.Status.RECEIVED, PurchaseOrder.Status.CANCELLED):
        raise ValidationError(f"{order} is already {order.get_status_display().lower()}.")
    order.status = PurchaseOrder.Status.CANCELLED
    order.save(update_fields=["status"])
    return order


def suggest_blend_inputs(recipe, quantity_made):
    """[(lot, grams)] for a batch, oldest best-by first for each component.
    Raises StockError if a component is short."""
    inputs = []
    for component in recipe.components_by_weight():
        needed = int((component.grams_per_kg * quantity_made / Decimal(1000)).to_integral_value(ROUND_HALF_UP))
        if needed <= 0:
            raise StockError(f"{component.item} rounds to 0 g in a {quantity_made:,} g batch; make a larger batch.")
        for lot in component.item.usable_lots():
            take = min(lot.quantity_on_hand, needed)
            inputs.append((lot, take))
            needed -= take
            if not needed:
                break
        if needed:
            raise StockError(f"Not enough {component.item} for this batch: {needed:,} g short.")
    return inputs


def check_blend(batch, inputs):
    """Raise ValidationError unless inputs ([(lot, grams)]) can make batch.

    Each input lot must be usable, of a component of the recipe, and hold
    enough; every component must be used; the best-by date must not be
    later than the earliest ingredient's.
    """
    recipe = batch.recipe
    components = {c.item_id: c for c in recipe.components.all()}
    if not components:
        raise ValidationError(f"Recipe {recipe} has no components.")
    total = recipe.total_grams_per_kg()
    if total != 1000:
        raise ValidationError(f"Recipe {recipe}'s components add up to {total} g per kg, not 1000.")
    errors = []
    used = {}
    for lot, grams in inputs:
        if lot.item_id not in components:
            errors.append(f"Lot {lot.code} is {lot.item}, which is not in recipe {recipe}.")
        if lot.status != Lot.Status.ACTIVE:
            errors.append(f"Lot {lot.code} is {lot.get_status_display().lower()} and cannot be used.")
        used[lot.pk] = used.get(lot.pk, 0) + grams
        if used[lot.pk] > lot.quantity_on_hand:
            errors.append(f"Lot {lot.code} has only {lot.quantity_on_hand:,} g.")
    missing = set(components) - {lot.item_id for lot, _ in inputs}
    for item_id in missing:
        errors.append(f"No lot given for {components[item_id].item}.")
    best_bys = [lot.best_by for lot, _ in inputs if lot.best_by]
    if batch.best_by and best_bys and batch.best_by > min(best_bys):
        errors.append(f"The best-by date can't be later than the earliest ingredient's ({min(best_bys):%Y-%m-%d}).")
    if errors:
        raise ValidationError(errors)


def make_blend(batch, inputs=None):
    """Make an unsaved BlendBatch (recipe, quantity_made, made_on, best_by,
    notes set) from inputs, [(lot, grams)]; None picks lots with
    suggest_blend_inputs().  Saves the batch and its inputs, takes the
    grams from the input lots, and makes the output lot, which takes its
    label facts from the inputs:

    - countries of origin, in order of weight;
    - organic only if every input is;
    - the allergens of every input, and their allergen statements;
    - ingredients in order of weight (the recipe's order);
    - landed cost per kg, the weighted cost of the inputs (blank if any
      input has none).
    """
    if inputs is None:
        inputs = suggest_blend_inputs(batch.recipe, batch.quantity_made)
    inputs = [(lot, int(grams)) for lot, grams in inputs if grams]
    with transaction.atomic():
        lots = {lot.pk: lot for lot in Lot.objects.select_for_update().filter(pk__in=[lot.pk for lot, _ in inputs])}
        inputs = [(lots[lot.pk], grams) for lot, grams in inputs]
        check_blend(batch, inputs)
        if not batch.made_on:
            batch.made_on = timezone.localdate()
        batch.save()
        for lot, grams in inputs:
            BlendInput.objects.create(batch=batch, lot=lot, quantity=grams)
            post_movement(lot, -grams, StockMovement.Kind.BLEND_INPUT, blend_batch=batch)
        output = _blend_lot(batch, inputs)
        batch.output_lot = output
        batch.save(update_fields=["output_lot"])
    return batch


def _blend_lot(batch, inputs):
    recipe = batch.recipe
    weight = {}
    for lot, grams in inputs:
        weight[lot.item_id] = weight.get(lot.item_id, 0) + grams
    by_weight = sorted(inputs, key=lambda pair: -weight[pair[0].item_id])

    countries = []
    for lot, _ in by_weight:
        if lot.item.kind in Item.GROWN:
            for country in (c.strip() for c in lot.country_of_origin.split(",")):
                if country and country not in countries:
                    countries.append(country)

    ingredients = []
    for component in recipe.components_by_weight():
        lot_words = [lot.ingredients for lot, _ in inputs if lot.item_id == component.item_id and lot.ingredients]
        words = lot_words[0] if lot_words else (component.item.ingredient_name or component.item.name)
        if words not in ingredients:
            ingredients.append(words)

    statements, seen = [], set()
    for lot, _ in by_weight:
        text = lot.allergen_statement.strip()
        if text and text not in seen:
            seen.add(text)
            statements.append(f"{lot.code}: {text}")

    cost = None
    if all(lot.landed_cost is not None for lot, _ in inputs):
        total = sum((lot.landed_cost * grams for lot, grams in inputs), Decimal(0)) / Decimal(1000)
        cost = (total * 1000 / batch.quantity_made).quantize(Decimal("0.01"), ROUND_HALF_UP)
    tariff = None
    if all(lot.tariff_cost is not None for lot, _ in inputs):
        total = sum((lot.tariff_cost * grams for lot, grams in inputs), Decimal(0)) / Decimal(1000)
        tariff = (total * 1000 / batch.quantity_made).quantize(Decimal("0.01"), ROUND_HALF_UP)

    best_bys = [lot.best_by for lot, _ in inputs if lot.best_by]
    output = Lot(
        item=recipe.output_item,
        source=Lot.Source.BLENDED,
        quantity_received=batch.quantity_made,
        received_on=batch.made_on,
        best_by=batch.best_by or (min(best_bys) if best_bys else None),
        country_of_origin=", ".join(countries)[:150],
        organic=all(lot.organic for lot, _ in inputs),
        ingredients=", ".join(ingredients)[:500],
        allergen_statement="\n".join(statements),
        landed_cost=cost,
        tariff_cost=tariff,
        notes=f"Blend batch {batch.pk} of {recipe}",
    )
    output.save()
    allergens = set()
    for lot, _ in inputs:
        allergens.update(lot.allergens.all())
    output.allergens.set(allergens)
    return output
