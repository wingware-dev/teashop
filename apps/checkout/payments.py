"""Payments through Stripe: the Payment Element in the customer's browser
takes the card (or Apple Pay, Google Pay, Link...) straight to Stripe, so
card data never reaches this server (PCI DSS SAQ A).

provider() gives the configured one (settings.PAYMENT_PROVIDER):

- StripePayments: Stripe's API with test keys until the owner approves
  live ones (STRIPE_ALLOW_LIVE).  STRIPE_API_BASE can point it at
  stripe-mock.
- FakePayments: a stand-in for laptops and tests, with a "pay" button that
  marks the order paid without any money moving; refused in production.

Stripe's webhook (webhooks.py) is what marks orders paid; the return page
also checks, so a slow webhook doesn't leave the customer waiting.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

log = logging.getLogger(__name__)


class PaymentError(Exception):
    """Stripe refused or could not be reached; the message is for the customer."""


@dataclass(frozen=True)
class PaymentStart:
    """What the browser needs to take a payment: the provider's id for it
    and the Payment Element's client secret."""

    id: str
    client_secret: str
    customer_id: str = ""


def stripe_client():
    base = {"api": settings.STRIPE_API_BASE} if settings.STRIPE_API_BASE else None
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY, base_addresses=base, max_network_retries=2)


def provider():
    if settings.PAYMENT_PROVIDER == "stripe":
        if not settings.STRIPE_SECRET_KEY:
            raise ImproperlyConfigured("PAYMENT_PROVIDER is stripe but STRIPE_SECRET_KEY is not set")
        return StripePayments()
    if settings.PRODUCTION:
        raise ImproperlyConfigured("The stand-in payment provider is not for production: set the Stripe keys")
    return FakePayments()


def is_configured():
    """Whether checkout can take payments here."""
    if settings.PAYMENT_PROVIDER == "stripe":
        return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_PUBLISHABLE_KEY and settings.STRIPE_WEBHOOK_SECRET)
    return not settings.PRODUCTION


def cents(amount):
    return int((Decimal(amount) * 100).to_integral_value())


def _stripe_address(holder):
    return {"line1": holder.ship_street1, "line2": holder.ship_street2 or None, "city": holder.ship_city,
            "state": holder.ship_state, "postal_code": holder.ship_zip, "country": "US"}


class FakePayments:
    """No money moves: the pay page shows a stand-in button instead of
    Stripe's fields (views.fake_pay)."""

    name = "fake"
    publishable_key = ""

    def start_payment(self, order):
        return PaymentStart(f"fake_pi_{order.number}", "")

    def payment_status(self, payment_id):
        return None, None

    def start_subscription(self, subscription):
        return PaymentStart(f"fake_sub_{subscription.pk}", "", f"fake_cus_{subscription.pk}")

    def cancel_subscription(self, subscription):
        log.info("Stand-in payments: subscription %s cancelled", subscription.pk)

    def record_tax(self, order):
        pass


class StripePayments:
    name = "stripe"

    def __init__(self, client=None):
        self.client = client or stripe_client()

    @property
    def publishable_key(self):
        return settings.STRIPE_PUBLISHABLE_KEY

    def start_payment(self, order):
        """A PaymentIntent for the order's total: a new one, or the order's
        own brought up to date if the customer came back and changed it."""
        params = {
            "amount": order.total_cents,
            "currency": "usd",
            "description": f"{settings.SHOP_NAME} order {order.number}",
            "metadata": {"order_number": order.number},
            "shipping": {"name": order.ship_name, "phone": order.ship_phone or None,
                         "address": _stripe_address(order)},
        }
        try:
            if order.payment_id.startswith("pi_"):
                intent = self.client.v1.payment_intents.update(
                    order.payment_id, params={k: params[k] for k in ("amount", "shipping")})
            else:
                intent = self.client.v1.payment_intents.create(
                    params={**params, "automatic_payment_methods": {"enabled": True}},
                    options={"idempotency_key": f"order-{order.number}-{order.pk}"})
        except stripe.StripeError as exc:
            log.error("Stripe refused a PaymentIntent for order %s: %s", order.number, exc)
            raise PaymentError("We could not start the payment.  Please try again in a minute.") from exc
        return PaymentStart(intent.id, intent.client_secret)

    def payment_status(self, payment_id):
        """(status, amount received in dollars) of a PaymentIntent."""
        try:
            intent = self.client.v1.payment_intents.retrieve(payment_id)
        except stripe.StripeError as exc:
            log.error("Could not read PaymentIntent %s: %s", payment_id, exc)
            return None, None
        return intent.status, Decimal(intent.amount_received or 0) / 100

    def _product_for(self, plan):
        if not plan.stripe_product_id:
            product = self.client.v1.products.create(params={
                "name": f"{settings.SHOP_NAME}: {plan.name}", "metadata": {"plan": plan.slug}},
                options={"idempotency_key": f"plan-{plan.pk}-product"})
            plan.stripe_product_id = product.id
            plan.save(update_fields=["stripe_product_id"])
        return plan.stripe_product_id

    def start_subscription(self, subscription):
        """A Stripe customer and subscription, its first invoice waiting for
        the Payment Element (payment_behavior default_incomplete)."""
        plan = subscription.plan
        interval = {"interval": "year", "interval_count": 1} if subscription.interval_months == 12 else {
            "interval": "month", "interval_count": subscription.interval_months}
        try:
            customer = self.client.v1.customers.create(params={
                "email": subscription.email, "name": subscription.ship_name,
                "shipping": {"name": subscription.ship_name, "address": _stripe_address(subscription)},
                "metadata": {"subscription": str(subscription.pk)},
            }, options={"idempotency_key": f"subscription-{subscription.pk}-customer"})
            created = self.client.v1.subscriptions.create(params={
                "customer": customer.id,
                "items": [{"price_data": {"currency": "usd", "product": self._product_for(plan),
                                          "unit_amount": cents(subscription.price), "recurring": interval}}],
                "payment_behavior": "default_incomplete",
                "payment_settings": {"save_default_payment_method": "on_subscription"},
                "metadata": {"subscription": str(subscription.pk)},
                "expand": ["latest_invoice.confirmation_secret"],
            }, options={"idempotency_key": f"subscription-{subscription.pk}-create"})
        except stripe.StripeError as exc:
            log.error("Stripe refused subscription %s: %s", subscription.pk, exc)
            raise PaymentError("We could not start the subscription.  Please try again in a minute.") from exc
        secret = created.latest_invoice.confirmation_secret.client_secret
        return PaymentStart(created.id, secret, customer.id)

    def cancel_subscription(self, subscription):
        """No further renewals; the period paid for runs out."""
        try:
            self.client.v1.subscriptions.update(subscription.stripe_subscription_id,
                                                params={"cancel_at_period_end": True})
        except stripe.StripeError as exc:
            log.error("Stripe could not cancel subscription %s: %s", subscription.pk, exc)
            raise PaymentError("We could not cancel just now.  Please try again, or write to us.") from exc

    def record_tax(self, order):
        """Tell Stripe Tax the sale happened, for its filing reports."""
        if not order.tax_calculation_id:
            return
        try:
            self.client.v1.tax.transactions.create_from_calculation(
                params={"calculation": order.tax_calculation_id, "reference": order.number})
        except stripe.StripeError:
            log.exception("Stripe Tax did not record the sale for order %s", order.number)


def parse_event(payload, signature):
    """The Stripe event in a webhook request, after checking its signature."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise PaymentError("STRIPE_WEBHOOK_SECRET is not set")
    try:
        return stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise PaymentError(f"Bad Stripe webhook: {exc}") from exc
