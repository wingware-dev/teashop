"""Packing, shipping, cancelling and refunding orders.

Everything the fulfillment pages do goes through here, so the rules hold
whoever acts: stock moves only through catalog.services.pack() and
reverse_package(), postage only through carriers.provider(), money back
only through refund(), which AI agents may not call.

Errors the owner should see raise FulfillmentError (a ValidationError).
"""

import logging
import math
from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_DOWN, Decimal

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.audit import agent_involved, record
from apps.catalog import services as catalog
from apps.catalog.models import Product
from apps.checkout import orders as checkout_orders
from apps.checkout import payments
from apps.checkout import shipping as checkout_shipping
from apps.checkout import tax as checkout_tax
from apps.checkout.models import Order, add_business_days
from apps.inventory import services as inventory
from apps.inventory.models import StockMovement

from . import boxes, carriers, emails
from .models import DelayNotice, PackedPackage, Parcel, ParcelLine, Pickup, PostageLabel, Refund

log = logging.getLogger(__name__)

CENT = Decimal("0.01")


class FulfillmentError(ValidationError):
    """The action can't be done as asked; the message is for the owner."""


class AllergenCheckNeeded(FulfillmentError):
    """The package's tea lot carries allergens and the packer has not yet
    confirmed allergen handling."""

    def __init__(self, allergens):
        self.allergens = allergens
        super().__init__(f"This tea contains {catalog.join_words(allergens)}.  Confirm the allergen handling "
                         f"(separate scoop, clean the bench afterwards) before packing it.")


def _refuse_agents(what):
    if agent_involved():
        raise PermissionDenied(f"AI agents cannot {what}; the owner does.")


# -- Parcels -------------------------------------------------------------

def parcels(order):
    """The order's parcels, making the first (the whole order) for a paid
    order that has none yet."""
    with transaction.atomic():
        if order.status == Order.Status.PAID and not order.parcels.exists():
            parcel = Parcel.objects.create(order=order, kind=Parcel.Kind.ORDER)
            ParcelLine.objects.bulk_create([ParcelLine(parcel=parcel, order_line=line, quantity=line.quantity)
                                            for line in order.lines.all()])
    return list(order.parcels.prefetch_related("lines__order_line__size_option__product").order_by("pk"))


def active_parcels(order):
    return [parcel for parcel in parcels(order) if parcel.is_active]


@dataclass
class LineProgress:
    line: ParcelLine
    packed: list  # PackedPackage, live

    @property
    def order_line(self):
        return self.line.order_line

    @property
    def size(self):
        return self.order_line.size_option

    @property
    def open_count(self):
        """Packages packed for a line without a fixed count (a subscription
        delivery's contents) are as many as the owner packs."""
        return self.size is None

    @property
    def remaining(self):
        if self.open_count:
            return 0 if self.packed else 1
        return max(self.line.quantity - len(self.packed), 0)

    @property
    def is_tea(self):
        return self.size is None or self.size.product.kind == Product.Kind.TEA

    @property
    def done(self):
        return self.remaining == 0


def progress(parcel):
    """[LineProgress] for the parcel's lines."""
    packed = {}
    for package in parcel.live_packages():
        packed.setdefault(package.order_line_id, []).append(package)
    return [LineProgress(line, packed.get(line.order_line_id, []))
            for line in parcel.lines.select_related("order_line__size_option__product__tea")]


def packed_sizes(parcel):
    """[(size_option, count)] of the parcel's live packages, or of what it
    will hold once packed, for the box suggestion."""
    counts = {}
    for row in progress(parcel):
        if row.packed:
            for package in row.packed:
                size = package.sold_package.size_option
                counts[size] = counts.get(size, 0) + 1
            if not row.open_count and row.remaining:
                counts[row.size] = counts.get(row.size, 0) + row.remaining
        elif row.size is not None:
            counts[row.size] = counts.get(row.size, 0) + row.line.quantity
    return list(counts.items())


def suggest_box(parcel):
    return boxes.suggest(packed_sizes(parcel))


# -- Packing -------------------------------------------------------------

def likely_lot(size):
    """The lot pack() would choose for one package of size now, or None."""
    if size.product.kind != Product.Kind.TEA:
        return None
    try:
        return inventory.pick_lot(size.product.tea, size.net_grams, lots=size.tea_lots())
    except inventory.StockError:
        return None


def allergens_of(lot):
    return [allergen.name for allergen in lot.allergens.all()] if lot else []


def _package_amount(order_line):
    """What the customer paid for one package of the line, after its
    share of the discount."""
    if order_line.size_option is None or not order_line.quantity:
        return None
    return (order_line.net_amount / order_line.quantity).quantize(CENT, ROUND_DOWN)


def pack_package(parcel, order_line, *, measured_grams=None, scale=None, user=None, lot=None, size=None,
                 allergens_confirmed=False):
    """Pack one package of order_line into parcel.

    Tea: measured_grams is the net weight the scale showed (at least the
    labelled net weight), on scale, a usable legal-for-trade Scale.  A lot
    carrying allergens needs allergens_confirmed.  size is for lines
    without one (subscription deliveries): which size to pack.

    Returns the PackedPackage.  Raises FulfillmentError, or StockError
    when stock is short (then nothing is taken)."""
    if not parcel.is_active:
        raise FulfillmentError(f"This parcel is {parcel.get_status_display().lower()}; nothing more can be packed.")
    order = parcel.order
    if order.status not in Order.PAID_STATUSES:
        raise FulfillmentError(f"Order {order.number} is {order.get_status_display().lower()}.")
    row = next((r for r in progress(parcel) if r.order_line.pk == order_line.pk), None)
    if row is None:
        raise FulfillmentError("That line is not in this parcel.")
    size = order_line.size_option or size
    if size is None:
        raise FulfillmentError("Choose which tea and size to pack for this delivery.")
    if not row.open_count and row.remaining <= 0:
        raise FulfillmentError(f"All {row.line.quantity} of {size} are packed already.")
    tea_grams = None
    if size.product.kind == Product.Kind.TEA:
        if scale is None:
            raise FulfillmentError("Choose the scale the tea was weighed on.")
        if not scale.usable:
            raise FulfillmentError(f"{scale} can't be used for packing: its seal is broken or it is retired.  "
                                   "Use a sealed scale.")
        if measured_grams is None:
            raise FulfillmentError("Enter the net weight the scale showed.")
        measured_grams = Decimal(measured_grams).quantize(Decimal("0.1"))
        if measured_grams < size.net_grams:
            raise FulfillmentError(f"{measured_grams} g is under the labelled {size.net_grams} g.  Add tea and "
                                   "weigh again.")
        if measured_grams > size.net_grams * Decimal("1.2"):
            raise FulfillmentError(f"{measured_grams} g is far over the labelled {size.net_grams} g.  Check the "
                                   "scale's tare and weigh again.")
        tea_grams = math.ceil(measured_grams)
        lot = lot or inventory.pick_lot(size.product.tea, tea_grams, lots=size.tea_lots())
        found = allergens_of(lot)
        if found and not allergens_confirmed:
            raise AllergenCheckNeeded(found)
    else:
        measured_grams = None
        scale = None
    amount = _package_amount(order_line) if order_line.size_option_id else size.price
    with transaction.atomic():
        sold = catalog.pack(size, order.number, amount=amount, lot=lot, tea_grams=tea_grams)
        packed = PackedPackage.objects.create(
            parcel=parcel, order_line=order_line, sold_package=sold, measured_grams=measured_grams, scale=scale,
            scale_serial=scale.serial_number if scale else "", scale_sealed_on=scale.sealed_on if scale else None,
            allergens_confirmed=bool(allergens_confirmed and sold.tea_lot_id and allergens_of(sold.tea_lot)),
            packed_by=user if user and user.is_authenticated else None,
        )
        record("fulfillment.packed", obj=order, message=(
            f"{size}" + (f": {measured_grams} g from lot {sold.tea_lot.code} on scale {scale.serial_number}"
                         if sold.tea_lot_id else "")))
    return packed


def unpack(package, note, *, reusable=True, user=None):
    """Undo a packed package of a parcel that has not shipped (a mistake,
    or the order is cancelled): stock goes back (catalog.reverse_package)."""
    if package.parcel.status == Parcel.Status.SHIPPED:
        raise FulfillmentError("That package has shipped; it can't be unpacked.")
    if package.reversed:
        raise FulfillmentError("That package was already unpacked.")
    with transaction.atomic():
        catalog.reverse_package(package.sold_package, note or "Unpacked", reusable=reusable)
        record("fulfillment.unpacked", obj=package.parcel.order,
               message=f"{package.sold_package.size_option}: {note}" + ("" if reusable else " (written off)"))


def mark_labels_printed(packages):
    now = timezone.now()
    PackedPackage.objects.filter(pk__in=[p.pk for p in packages], label_printed_at=None).update(label_printed_at=now)


# -- Postage -------------------------------------------------------------

def _box_needs(box):
    needs = [(box.item, 1)]
    if box.filler_id and box.filler_quantity:
        needs.append((box.filler, box.filler_quantity))
    return needs


def buy_label(parcel, *, weight_grams, service, box=None, box_description="", dimensions=None, user=None,
              ship_partial=False, suggested=None):
    """Buy postage for the parcel and ship it.

    box (a BoxSize) is the box used; its stock and its filler's go down.  A
    box not on the list: box_description and dimensions (inches).  Lines
    not fully packed raise, unless ship_partial: then they move to a new
    back-ordered parcel.

    Returns (label, warnings)."""
    order = parcel.order
    if not parcel.is_active:
        raise FulfillmentError(f"This parcel is {parcel.get_status_display().lower()}.")
    if order.status not in Order.PAID_STATUSES:
        raise FulfillmentError(f"Order {order.number} is {order.get_status_display().lower()}.")
    if parcel.current_label():
        raise FulfillmentError("This parcel already has a label.  Void it first to buy another.")
    rows = progress(parcel)
    if not any(row.packed for row in rows):
        raise FulfillmentError("Pack something before buying the label.")
    unpacked = [row for row in rows if row.remaining and not row.open_count]
    if unpacked and not ship_partial:
        raise FulfillmentError("Not everything is packed.  Pack the rest, or ship what is packed and back-order "
                               "the rest.")
    weight_grams = int(weight_grams or 0)
    if weight_grams <= 0:
        raise FulfillmentError("Weigh the parcel and enter its weight.")
    if box is not None:
        dimensions = [box.length_in, box.width_in, box.height_in]
        for item, quantity in _box_needs(box):
            if item.on_hand() < quantity:
                raise FulfillmentError(f"No {item} in stock.  Choose the box you actually used, or record a "
                                       "delivery of boxes first.")
    elif not box_description:
        raise FulfillmentError("Choose the box, or describe the one you used.")
    if not order.has_address:
        raise FulfillmentError("The order has no shipping address.")

    provider = carriers.provider()
    try:
        purchase = provider.buy(order, weight_grams=weight_grams, dimensions=dimensions, service=service,
                                label_format=settings.SHIPPING_LABEL_FORMAT)
    except carriers.CarrierError as exc:
        raise FulfillmentError(str(exc)) from exc
    warnings = []
    with transaction.atomic():
        label = PostageLabel(
            parcel=parcel, provider=provider.name, test_mode=purchase.test_mode, shipment_id=purchase.shipment_id,
            carrier=purchase.carrier, service=purchase.service, tracking_number=purchase.tracking_number,
            postage=purchase.postage, weight_grams=weight_grams, box=box, box_suggested=suggested,
            box_description="" if box else box_description[:120],
            length_in=dimensions[0] if dimensions else None, width_in=dimensions[1] if dimensions else None,
            height_in=dimensions[2] if dimensions else None, label_format=purchase.label_format,
            bought_by=user if user and user.is_authenticated else None,
        )
        extension = "zpl" if purchase.label_format == "ZPL" else "pdf"
        label.label_file.save(f"{order.number}-{purchase.tracking_number}.{extension}", ContentFile(purchase.label),
                              save=False)
        label.save()
        if box is not None:
            for item, quantity in _box_needs(box):
                try:
                    inventory.consume(item, quantity, reference=order.number, note=f"label {label.pk}")
                except inventory.StockError as exc:
                    log.warning("Label %s bought but box stock could not go down: %s", label.pk, exc)
                    warnings.append(f"The label is bought, but {item} stock could not go down: {exc.messages[0]}  "
                                    "Correct it with a stock adjustment.")
        rest = []
        if unpacked:
            backorder = Parcel.objects.create(order=order, kind=Parcel.Kind.BACKORDER, status=Parcel.Status.BACKORDERED,
                                              reason="Not in stock when the rest shipped")
            for row in unpacked:
                ParcelLine.objects.create(parcel=backorder, order_line=row.order_line, quantity=row.remaining)
                row.line.quantity -= row.remaining
                if row.line.quantity:
                    row.line.save(update_fields=["quantity"])
                else:
                    row.line.delete()
            rest = list(backorder.lines.select_related("order_line"))
        parcel.status = Parcel.Status.SHIPPED
        parcel.shipped_at = timezone.now()
        parcel.save(update_fields=["status", "shipped_at"])
        record("fulfillment.label_bought", obj=order, message=(
            f"{purchase.service} {purchase.tracking_number}, ${purchase.postage:,.2f}"
            + (" (test label)" if purchase.test_mode else "") + f", {label.box_text}, {weight_grams} g"))
    _tell_customer_shipped(parcel, label, rest)
    return label, warnings


def _tell_customer_shipped(parcel, label, rest):
    order = parcel.order
    if parcel.kind == Parcel.Kind.RESHIP:
        Order.objects.filter(pk=order.pk).update(tracking_number=label.tracking_number, carrier=label.carrier)
        emails.reshipped(order, label, parcel.reason)
    elif rest or any(p.is_active for p in order.parcels.exclude(pk=parcel.pk)):
        Order.objects.filter(pk=order.pk).update(tracking_number=label.tracking_number, carrier=label.carrier)
        emails.part_shipped(order, label, rest or [line for p in order.parcels.filter(
            status__in=Parcel.ACTIVE_STATUSES) for line in p.lines.select_related("order_line")])
    else:
        checkout_orders.mark_shipped(order, label.tracking_number, label.carrier)


def void_label(label, user=None):
    """Ask for the postage back for a label that won't be used.  The box
    and filler go back to stock and the parcel can be labelled again."""
    if label.voided_at:
        raise FulfillmentError("That label is already voided.")
    if label.provider != carriers.provider().name:
        raise FulfillmentError(f"The label was bought through {label.provider}; void it there.")
    try:
        status = carriers.provider().void(label.shipment_id)
    except carriers.CarrierError as exc:
        raise FulfillmentError(str(exc)) from exc
    order = label.parcel.order
    with transaction.atomic():
        label.voided_at = timezone.now()
        label.void_status = status[:30]
        label.save(update_fields=["voided_at", "void_status"])
        for movement in StockMovement.objects.filter(reference=order.number, note=f"label {label.pk}",
                                                     kind=StockMovement.Kind.SALE).select_related("lot"):
            inventory.post_movement(movement.lot, -movement.quantity, StockMovement.Kind.ADJUSTMENT,
                                    reason=StockMovement.Reason.RETURNED, reference=order.number,
                                    note=f"label {label.pk} voided")
        parcel = label.parcel
        parcel.status = Parcel.Status.OPEN
        parcel.shipped_at = None
        parcel.save(update_fields=["status", "shipped_at"])
        if order.status == Order.Status.SHIPPED and order.tracking_number == label.tracking_number:
            Order.objects.filter(pk=order.pk).update(
                status=Order.Status.PAID if parcel.kind != Parcel.Kind.RESHIP else Order.Status.SHIPPED,
                tracking_number="", shipped_at=None if parcel.kind != Parcel.Kind.RESHIP else order.shipped_at)
        record("fulfillment.label_voided", obj=order, message=f"{label.tracking_number}: {status}")
    return label


# -- Address changes ------------------------------------------------------

def change_address(order, address, *, accept_unverified=False, user=None):
    """Ship the order's unshipped parcels to address (a checkout Address),
    checked with the post office.  Returns the Verification."""
    if order.status not in Order.PAID_STATUSES:
        raise FulfillmentError(f"Order {order.number} is {order.get_status_display().lower()}.")
    if not active_parcels(order):
        raise FulfillmentError("Everything in this order has shipped; the address can't change now.")
    if any(parcel.current_label() for parcel in active_parcels(order)):
        raise FulfillmentError("Void the label first: it has the old address on it.")
    try:
        checked = checkout_shipping.provider().verify(address)
    except checkout_shipping.ShippingError as exc:
        raise FulfillmentError(str(exc)) from exc
    if not checked.ok and not accept_unverified:
        raise FulfillmentError("The post office does not know this address: " + " ".join(checked.messages)
                               + "  Tick \"Use it anyway\" if you are sure.")
    old = ", ".join(order.address_lines())
    with transaction.atomic():
        order.set_address(checked.address if checked.ok else address)
        order.address_verified = checked.ok
        order.save()
        record("fulfillment.address_changed", obj=order,
               message=f"From {old} to {', '.join(order.address_lines())}")
    return checked


# -- Money back -----------------------------------------------------------

def refunded(order):
    return order.refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")


def refundable(order):
    paid = order.amount_received if order.amount_received is not None else order.total
    return max(paid - refunded(order), Decimal("0.00"))


def _payment_provider(order):
    current = payments.provider()
    if order.payment_provider and order.payment_provider != current.name:
        if order.payment_provider == "fake" and not settings.PRODUCTION:
            return payments.FakePayments()
        raise FulfillmentError(f"Order {order.number} was paid through {order.payment_provider}; refund it there.")
    return current


def refund(order, amount, reason, *, user=None, kind=None, email=True, items=None, shipping=False):
    """Give amount (dollars) of the order's payment back.  Only the owner
    may: AI agents are refused.  items {OrderLine: quantity} and shipping
    say what it is for, which decides the sales tax given back with it
    (checkout.tax.refund_tax; neither: the order as a whole).  Returns the
    Refund."""
    _refuse_agents("give refunds")
    amount = Decimal(amount).quantize(CENT)
    if order.status not in (*Order.PAID_STATUSES, Order.Status.CANCELLED):
        raise FulfillmentError(f"Order {order.number} was never paid.")
    if not reason.strip():
        raise FulfillmentError("Say why, for the customer and your records.")
    available = refundable(order)
    if amount <= 0:
        raise FulfillmentError("Enter the amount to refund.")
    if amount > available:
        raise FulfillmentError(f"At most ${available:,.2f} is left to refund on this order.")
    if any(line.order_id != order.pk for line in items or {}):
        raise FulfillmentError("Those items are not in this order.")
    earlier = order.refunds.aggregate(amount=Sum("amount"), taxable=Sum("taxable_amount"), tax=Sum("tax_amount"))
    try:
        taxable, tax = checkout_tax.refund_tax(
            order, amount, items=items, shipping=shipping,
            before=tuple(earlier[key] or Decimal("0.00") for key in ("amount", "taxable", "tax")))
    except checkout_tax.RefundTaxError as exc:
        raise FulfillmentError(str(exc)) from exc
    kind = kind or (Refund.Kind.FULL if amount == available and not order.refunds.exists() else Refund.Kind.PARTIAL)
    provider = _payment_provider(order)
    number = order.refunds.count() + 1
    try:
        provider_id = provider.refund(order, amount, f"{order.number}-{number}-{payments.cents(amount)}")
    except payments.PaymentError as exc:
        raise FulfillmentError(str(exc)) from exc
    refund = Refund.objects.create(order=order, kind=kind, amount=amount, taxable_amount=taxable, tax_amount=tax,
                                   reason=reason.strip()[:300],
                                   provider=provider.name, provider_id=provider_id,
                                   created_by=user if user and user.is_authenticated else None)
    record("fulfillment.refunded", obj=order, message=f"${amount:,.2f} ({refund.get_kind_display()}): {reason}")
    if email:
        emails.refund_sent(refund)  # queued; sets refund.email_sent_at once sent
    return refund


def cancel_order(order, reason, *, user=None, reusable=True, by_customer=False):
    """Cancel an order that has not shipped: what was packed goes back to
    stock, everything paid is refunded, and the customer is told."""
    if by_customer:
        actor_reason = reason or "Cancelled at your request"
    else:
        _refuse_agents("cancel orders")
        actor_reason = reason
    if order.status != Order.Status.PAID:
        raise FulfillmentError(f"Order {order.number} is {order.get_status_display().lower()}; only an order "
                               "waiting to ship can be cancelled.  Refund a shipped order instead.")
    if any(parcel.status == Parcel.Status.SHIPPED for parcel in parcels(order)):
        raise FulfillmentError("Part of this order has shipped.  Refund the rest instead of cancelling.")
    if any(parcel.current_label() for parcel in parcels(order)):
        raise FulfillmentError("Void the label first.")
    if not actor_reason.strip():
        raise FulfillmentError("Say why the order is cancelled.")
    amount = refundable(order)
    if amount > 0:
        refund(order, amount, actor_reason, user=user, kind=Refund.Kind.CANCELLATION, email=False)
    with transaction.atomic():
        for parcel in parcels(order):
            for package in parcel.live_packages():
                catalog.reverse_package(package.sold_package, f"Order cancelled: {actor_reason}"[:300],
                                        reusable=reusable)
            parcel.status = Parcel.Status.CANCELLED
            parcel.save(update_fields=["status"])
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
        record("fulfillment.cancelled", obj=order,
               message=("By the customer: " if by_customer else "") + actor_reason)
    emails.order_cancelled(order, amount, actor_reason)
    return amount


# -- Reships and back-orders -----------------------------------------------

def start_reship(order, quantities, reason, user=None):
    """A new parcel resending {order_line: quantity} of a shipped order
    (lost or damaged).  It is packed and labelled like any parcel; the
    customer pays nothing."""
    if order.status not in Order.PAID_STATUSES or not order.parcels.filter(status=Parcel.Status.SHIPPED).exists():
        raise FulfillmentError("Only a parcel that has shipped can be reshipped.")
    quantities = {line: int(qty) for line, qty in quantities.items() if qty and int(qty) > 0}
    if not quantities:
        raise FulfillmentError("Choose what to send again.")
    for line, qty in quantities.items():
        if line.order_id != order.pk or qty > line.quantity:
            raise FulfillmentError(f"At most {line.quantity} of {line.product_name} can be sent again.")
    if not reason.strip():
        raise FulfillmentError("Say why it is sent again (lost, damaged...).")
    with transaction.atomic():
        parcel = Parcel.objects.create(order=order, kind=Parcel.Kind.RESHIP, reason=reason.strip()[:300])
        for line, qty in quantities.items():
            ParcelLine.objects.create(parcel=parcel, order_line=line, quantity=qty)
        record("fulfillment.reship_started", obj=order, message=reason)
    return parcel


def backorder(parcel, expected_on, reason):
    if not parcel.is_active or parcel.current_label():
        raise FulfillmentError("Only a parcel waiting to ship can be back-ordered.")
    parcel.status = Parcel.Status.BACKORDERED
    parcel.expected_on = expected_on
    parcel.reason = (reason or "Waiting for stock")[:300]
    parcel.save(update_fields=["status", "expected_on", "reason"])
    record("fulfillment.backordered", obj=parcel.order, message=f"{parcel.reason}; expected {expected_on or '?'}")


def resume(parcel):
    if parcel.status == Parcel.Status.BACKORDERED:
        parcel.status = Parcel.Status.OPEN
        parcel.save(update_fields=["status"])


# -- The Mail Order Rule ----------------------------------------------------

def first_promise(order):
    """The ship date the customer was first promised."""
    first = order.delay_notices.order_by("created_at", "pk").first()
    return first.old_ship_by if first else order.ship_by


def send_delay_notice(order, new_ship_by, reason, user=None):
    """Tell the customer the order ships later (16 CFR 435.2(b)): the new
    date, and the offer to cancel for a full refund.  A first notice of a
    delay of up to 30 days takes silence as consent, so the promised date
    moves now; a longer delay, or a second notice, needs the customer to
    agree, else the order is cancelled and refunded by answer_by."""
    if order.status != Order.Status.PAID:
        raise FulfillmentError(f"Order {order.number} is {order.get_status_display().lower()}.")
    today = timezone.localdate()
    if new_ship_by <= max(order.ship_by or today, today):
        raise FulfillmentError("The new date must be later than the promised date and today.")
    if not reason.strip():
        raise FulfillmentError("Say why, in words for the customer.")
    promised = first_promise(order) or today
    later = (new_ship_by - promised).days
    needs_consent = order.delay_notices.exists() or later > settings.MAIL_ORDER_IMPLIED_CONSENT_DAYS
    answer_by = max(order.ship_by or today, add_business_days(today, 3)) if needs_consent else None
    with transaction.atomic():
        notice = DelayNotice.objects.create(order=order, old_ship_by=order.ship_by or today, new_ship_by=new_ship_by,
                                            reason=reason.strip()[:300], needs_consent=needs_consent,
                                            answer_by=answer_by)
        if not needs_consent:
            order.ship_by = new_ship_by
            order.save(update_fields=["ship_by"])
        record("fulfillment.delay_notice", obj=order, message=(
            f"New date {new_ship_by:%Y-%m-%d}" + (", needs the customer's consent" if needs_consent else "")))
    emails.delay_notice(notice)  # queued; sets notice.sent_at once sent
    return notice


def answer_delay(notice, wait):
    """The customer's answer to a delay notice: wait, or cancel for a full
    refund."""
    order = notice.order
    if order.status != Order.Status.PAID:
        return notice
    if wait:
        if notice.response != DelayNotice.Response.WAITING:
            return notice
        with transaction.atomic():
            notice.response = DelayNotice.Response.CONSENTED
            notice.responded_at = timezone.now()
            notice.save(update_fields=["response", "responded_at"])
            if notice.needs_consent and order.status == Order.Status.PAID:
                order.ship_by = notice.new_ship_by
                order.save(update_fields=["ship_by"])
            record("fulfillment.delay_consented", obj=order, message=f"Waits until {notice.new_ship_by:%Y-%m-%d}")
        return notice
    cancel_order(order, "You chose to cancel when we told you of the delay.", by_customer=True)
    notice.response = DelayNotice.Response.CANCELLED
    notice.responded_at = timezone.now()
    notice.save(update_fields=["response", "responded_at"])
    return notice


def consent_overdue(day=None):
    """Delay notices needing consent whose answer date has passed with no
    answer: the order must be cancelled and refunded."""
    day = day or timezone.localdate()
    return DelayNotice.objects.filter(needs_consent=True, response=DelayNotice.Response.WAITING, answer_by__lt=day,
                                      order__status=Order.Status.PAID).select_related("order")


# -- Pickups ---------------------------------------------------------------

def labels_for_pickup():
    """Labels bought and not voided, not in a pickup yet, from the last
    few days."""
    since = timezone.now() - timedelta(days=4)
    return PostageLabel.objects.filter(voided_at=None, pickup=None, bought_at__gte=since).select_related("parcel__order")


def next_pickup_day(day=None):
    """The next day USPS picks up (Monday to Saturday), after today."""
    day = (day or timezone.localdate()) + timedelta(days=1)
    while day.weekday() == 6:
        day += timedelta(days=1)
    return day


def schedule_pickup(day, *, location, instructions="", user=None):
    """Book a free USPS carrier pickup on day for the labels waiting."""
    waiting = list(labels_for_pickup())
    if not waiting:
        raise FulfillmentError("No labelled parcels are waiting for a pickup.")
    if day <= timezone.localdate() or day.weekday() == 6:
        raise FulfillmentError("Choose a day after today, Monday to Saturday.")
    if Pickup.objects.filter(pickup_date=day, status=Pickup.Status.SCHEDULED).exists():
        raise FulfillmentError(f"A pickup is already booked for {day:%A, %B %-d}; its parcels can join it.")
    provider = carriers.provider()
    try:
        booked = provider.schedule_pickup(day, shipment_id=waiting[0].shipment_id, location=location,
                                          instructions=instructions, reference=f"pickup-{day:%Y%m%d}")
    except carriers.CarrierError as exc:
        raise FulfillmentError(str(exc)) from exc
    with transaction.atomic():
        pickup = Pickup.objects.create(pickup_date=day, location=location[:60], instructions=instructions[:200],
                                       provider=provider.name, provider_id=booked.id, confirmation=booked.confirmation)
        PostageLabel.objects.filter(pk__in=[label.pk for label in waiting]).update(pickup=pickup)
        record("fulfillment.pickup_scheduled", obj=pickup, message=f"{len(waiting)} parcels, {booked.confirmation}")
    return pickup


def add_to_pickup(pickup):
    """Put the labels waiting into an already booked pickup (USPS takes
    every parcel left out)."""
    count = labels_for_pickup().update(pickup=pickup)
    return count


def cancel_pickup(pickup):
    if pickup.status != Pickup.Status.SCHEDULED:
        raise FulfillmentError("That pickup is not scheduled.")
    try:
        carriers.provider().cancel_pickup(pickup.provider_id)
    except carriers.CarrierError as exc:
        raise FulfillmentError(str(exc)) from exc
    with transaction.atomic():
        pickup.status = Pickup.Status.CANCELLED
        pickup.save(update_fields=["status"])
        pickup.labels.update(pickup=None)
        record("fulfillment.pickup_cancelled", obj=pickup)
