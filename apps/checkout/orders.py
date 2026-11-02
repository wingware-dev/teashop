"""Turning a cart into an order, and an order's life after: paid, shipped.

The checkout keeps its progress in the session (CheckoutState): the email,
the checked address, the rates quoted and the one chosen.  build_order()
fixes the figures in an Order waiting for payment; mark_paid() is called
by Stripe's webhook or the return page (whichever comes first; the second
does nothing) and sends the emails.
"""

import logging
from dataclasses import asdict, dataclass, field
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit import record

from . import emails
from . import payments as payment_providers
from .cart import cart_items, problems
from .models import Cart, CheckoutSettings, Order, OrderLine
from .pricing import quote
from .shipping import Address, Rate

log = logging.getLogger(__name__)

STATE_KEY = "checkout_state"


class OrderError(Exception):
    """The order cannot be placed as it is; the message is for the customer."""


@dataclass
class CheckoutState:
    """The checkout's progress, kept in the session."""

    email: str = ""
    address: dict = field(default_factory=dict)
    address_verified: bool = False
    rates: list = field(default_factory=list)
    rate_id: str = ""
    order_id: int = None

    @classmethod
    def load(cls, request):
        data = request.session.get(STATE_KEY) or {}
        known = {name: data[name] for name in cls.__dataclass_fields__ if name in data}
        return cls(**known)

    def save(self, request):
        request.session[STATE_KEY] = asdict(self)

    @staticmethod
    def clear(request):
        request.session.pop(STATE_KEY, None)

    @property
    def ship_to(self):
        return Address(**self.address) if self.address else None

    def rate_list(self):
        return [Rate(**{**rate, "amount": Decimal(rate["amount"])}) for rate in self.rates]

    def set_rates(self, rates):
        self.rates = [{**asdict(rate), "amount": str(rate.amount)} for rate in rates]
        if self.rate_id not in {rate.id for rate in rates}:
            self.rate_id = rates[0].id if rates else ""

    def chosen_rate(self):
        return next((rate for rate in self.rate_list() if rate.id == self.rate_id), None)


def build_order(cart, state, customer=None):
    """The order (waiting for payment) for cart and the checkout state,
    made or brought up to date; raises OrderError."""
    found = problems(cart)
    if found:
        raise OrderError(found[0][1])
    items = cart_items(cart)
    if not items:
        raise OrderError("Your cart is empty.")
    rate = state.chosen_rate()
    if rate is None or state.ship_to is None:
        raise OrderError("Please choose how to ship your order.")
    if not CheckoutSettings.current().taking_orders():
        raise OrderError("We are not taking orders just now.  Please come back soon.")
    figures = quote(items, discount=cart.discount, email=state.email, rates=state.rate_list(), rate=rate,
                    address=state.ship_to)
    if figures.discount_problem:
        cart.discount = None
        cart.save(update_fields=["discount"])
        raise OrderError(figures.discount_problem)

    with transaction.atomic():
        order = None
        if state.order_id:
            order = Order.objects.select_for_update().filter(pk=state.order_id, status=Order.Status.PENDING).first()
        order = order or Order()
        order.email = state.email
        order.customer = customer
        order.cart_id = cart.pk
        order.set_address(state.ship_to)
        order.address_verified = state.address_verified
        order.subtotal = figures.subtotal
        order.discount = figures.discount
        order.discount_code = figures.discount.code if figures.discount else ""
        order.discount_amount = figures.discount_amount
        order.shipping_service = rate.label
        order.shipping_rate_id = rate.id
        order.shipping_shipment_id = rate.shipment_id
        order.shipping_cost = figures.shipping_cost
        order.shipping_amount = figures.shipping_amount
        order.tax_rate = figures.tax.rate
        order.taxable_amount = figures.tax.taxable_amount
        order.tax_amount = figures.tax.tax
        order.tax_jurisdiction = figures.tax.jurisdiction
        order.tax_fallback = figures.tax.fallback
        order.tax_calculation_id = figures.tax.calculation_id
        order.total = figures.total
        order.save()
        order.lines.all().delete()
        OrderLine.objects.bulk_create([
            OrderLine(order=order, size_option=line.size, product_name=line.size.product.name,
                      size_name=line.size.name, sku=line.size.sku,
                      kind=OrderLine.Kind.GOODS if line.taxable else OrderLine.Kind.TEA,
                      unit_price=line.unit_price, quantity=line.quantity, line_total=line.line_total,
                      discount_share=line.discount_share, taxable=line.taxable)
            for line in figures.lines
        ])
    state.order_id = order.pk
    return order


def start_payment(order):
    """Ask the payment provider for the payment; returns PaymentStart."""
    provider = payment_providers.provider()
    started = provider.start_payment(order)
    order.payment_provider = provider.name
    order.payment_id = started.id
    order.save(update_fields=["payment_provider", "payment_id"])
    return started


def mark_paid(order, amount_received=None):
    """Record that the order is paid (once), then send the emails.
    Returns True if this call made it paid."""
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.is_paid:
            return False
        if order.status == Order.Status.CANCELLED:
            log.error("Payment arrived for cancelled order %s", order.number)
            emails.owner_notice(f"Payment for cancelled order {order.number}",
                                "A payment arrived for an order marked cancelled.  Refund it in Stripe.", order)
            return False
        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.ship_by = CheckoutSettings.current().ship_by()
        if amount_received is not None:
            order.amount_received = amount_received
        order.save()
        if order.cart_id:
            Cart.objects.filter(pk=order.cart_id).delete()
        record("checkout.order_paid", obj=order, message=f"${order.total:,.2f} via {order.payment_provider}")
    if amount_received is not None and amount_received != order.total:
        log.error("Order %s: received %s, total %s", order.number, amount_received, order.total)
        emails.owner_notice(f"Payment for order {order.number} does not match",
                            f"Stripe received ${amount_received:,.2f}; the order's total is ${order.total:,.2f}.  "
                            f"Check it before shipping.", order)
    after_paid(order)
    return True


def after_paid(order):
    emails.order_confirmation(order)
    emails.owner_new_order(order)
    if order.payment_provider == "stripe":
        payment_providers.provider().record_tax(order)


def mark_shipped(order, tracking_number, carrier="USPS"):
    """Record the parcel's tracking number and tell the customer."""
    order.status = Order.Status.SHIPPED
    order.shipped_at = order.shipped_at or timezone.now()
    order.tracking_number = tracking_number.strip()
    order.carrier = carrier
    order.save(update_fields=["status", "shipped_at", "tracking_number", "carrier"])
    record("checkout.order_shipped", obj=order, message=f"{carrier} {order.tracking_number}")
    return emails.order_shipped(order)
