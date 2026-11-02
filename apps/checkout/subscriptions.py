"""Tea subscriptions under New York's automatic renewal law (GBL 527-a)
and California's (Bus. & Prof. Code 17600-17606):

- the renewal terms sit right next to the sign-up button, and the
  customer ticks a box agreeing to them (views; the text agreed to is kept
  on the subscription);
- an acknowledgment email with the terms and how to cancel follows the
  first payment (emails.subscription_acknowledgment);
- terms of a year or more get a reminder 15 to 45 days before each renewal
  (send_reminders(), run daily by the send_subscription_reminders
  command); there are no free trials, and a price change applies only to
  new subscribers, so no other notices are due;
- cancelling is one button online, from the account page or the link in
  every subscription email, no sign-in needed (cancel()).

Billing is Stripe's: each renewal's paid invoice arrives by webhook and
becomes a delivery order (record_payment()).
"""

import logging
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from django.db import transaction
from django.utils import timezone

from apps.audit import record

from . import emails
from . import payments as payment_providers
from .models import CheckoutSettings, Order, OrderLine, Subscription

log = logging.getLogger(__name__)

# Reminders for terms of a year or more go this many days before renewal
# (the law's window is 15 to 45 days).
REMINDER_DAYS = 30
REMINDER_WINDOW = (15, 45)


def start(plan, email, address, customer=None):
    """A pending subscription (consent given now) and the PaymentStart for
    its first payment."""
    subscription = Subscription(plan=plan, customer=customer, email=email.strip().lower(), price=plan.price,
                                interval_months=plan.interval_months, terms_text=plan.renewal_terms(),
                                consented_at=timezone.now())
    subscription.set_address(address)
    subscription.save()
    provider = payment_providers.provider()
    started = provider.start_subscription(subscription)
    subscription.payment_provider = provider.name
    subscription.stripe_subscription_id = started.id
    subscription.stripe_customer_id = started.customer_id
    subscription.save(update_fields=["payment_provider", "stripe_subscription_id", "stripe_customer_id"])
    record("checkout.subscription_started", obj=subscription,
           message=f"Consent to: {subscription.terms_text}")
    return subscription, started


def _next_period_end(subscription, start=None):
    start = start or timezone.now()
    months = subscription.interval_months
    month = start.month - 1 + months
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, 28)
    return start.replace(year=year, month=month, day=day)


def record_payment(subscription, *, first, period_end=None, invoice_id="", amount=None):
    """A paid invoice: activate the subscription (first) and make the
    delivery order.  Returns the order, or None if already recorded."""
    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)
        if invoice_id and Order.objects.filter(subscription=subscription, payment_id=invoice_id).exists():
            return None
        if first and subscription.status != Subscription.Status.PENDING:
            return None
        if subscription.status in (Subscription.Status.PENDING, Subscription.Status.PAST_DUE):
            subscription.status = Subscription.Status.ACTIVE
        subscription.current_period_end = period_end or _next_period_end(subscription)
        subscription.save(update_fields=["status", "current_period_end"])
        number = subscription.orders.count() + 1
        price = amount if amount is not None else subscription.price
        order = Order(email=subscription.email, customer=subscription.customer, subscription=subscription,
                      status=Order.Status.PAID, subtotal=price, total=price, paid_at=timezone.now(),
                      ship_by=CheckoutSettings.current().ship_by(), payment_provider=subscription.payment_provider,
                      payment_id=invoice_id, amount_received=price, address_verified=True,
                      tax_jurisdiction="Tea only: no sales tax")
        order.set_address(subscription.address)
        order.save()
        OrderLine.objects.create(order=order, kind=OrderLine.Kind.SUBSCRIPTION, product_name=subscription.plan.name,
                                 size_name=f"Delivery {number}", unit_price=price, quantity=1, line_total=price)
        record("checkout.subscription_paid", obj=subscription, message=f"Delivery {number}: order {order.number}")
    if first:
        emails.subscription_acknowledgment(subscription)
    else:
        emails.order_confirmation(order)
    emails.owner_new_order(order)
    return order


def payment_failed(subscription):
    if subscription.status != Subscription.Status.ACTIVE:
        return
    subscription.status = Subscription.Status.PAST_DUE
    subscription.save(update_fields=["status"])
    record("checkout.subscription_payment_failed", obj=subscription)
    emails.subscription_payment_failed(subscription)


def cancel(subscription, by="customer"):
    """Stop all future renewals.  Returns False if there was nothing to
    cancel.  Raises payments.PaymentError if Stripe can't be reached."""
    if subscription.status == Subscription.Status.PENDING:
        subscription.status = Subscription.Status.ENDED
        subscription.cancelled_at = timezone.now()
        subscription.save(update_fields=["status", "cancelled_at"])
        return True
    if not subscription.is_live:
        return False
    if subscription.payment_provider == "stripe" and subscription.stripe_subscription_id:
        payment_providers.provider().cancel_subscription(subscription)
    subscription.status = Subscription.Status.CANCELLED
    subscription.cancelled_at = timezone.now()
    subscription.save(update_fields=["status", "cancelled_at"])
    record("checkout.subscription_cancelled", obj=subscription, message=f"Cancelled by {by}")
    emails.subscription_cancelled(subscription)
    return True


def _stripe_period_end(stripe_subscription):
    """The end of the current period: on the subscription's item in recent
    API versions, on the subscription itself in older ones."""
    items = (stripe_subscription.get("items") or {}).get("data") or []
    stamp = (items[0].get("current_period_end") if items else None) or stripe_subscription.get("current_period_end")
    return datetime.fromtimestamp(stamp, tz=dt_timezone.utc) if stamp else None


def sync_from_stripe(subscription, stripe_subscription):
    """Bring status and renewal date in line with Stripe's subscription."""
    period_end = _stripe_period_end(stripe_subscription)
    if period_end:
        subscription.current_period_end = period_end
    status = stripe_subscription.get("status")
    if status == "canceled":
        subscription.status = Subscription.Status.ENDED
    elif status in ("past_due", "unpaid") and subscription.status == Subscription.Status.ACTIVE:
        subscription.status = Subscription.Status.PAST_DUE
    elif status == "active" and subscription.status == Subscription.Status.PAST_DUE:
        subscription.status = Subscription.Status.ACTIVE
    subscription.save(update_fields=["current_period_end", "status"])


def needs_reminder(subscription, now=None):
    now = now or timezone.now()
    if subscription.status != Subscription.Status.ACTIVE or not subscription.current_period_end:
        return False
    if subscription.interval_months < 12 or subscription.reminded_for == subscription.current_period_end:
        return False
    days_left = (subscription.current_period_end - now) / timedelta(days=1)
    return REMINDER_WINDOW[0] <= days_left <= REMINDER_DAYS


def send_reminders(now=None):
    """Send the renewal reminders due; returns how many were sent."""
    sent = 0
    for subscription in Subscription.objects.filter(status=Subscription.Status.ACTIVE, interval_months__gte=12):
        if needs_reminder(subscription, now) and emails.subscription_reminder(subscription):
            subscription.reminded_for = subscription.current_period_end
            subscription.save(update_fields=["reminded_for"])
            sent += 1
    return sent


def reminders_overdue(now=None):
    """Active yearly subscriptions now inside the law's window without a
    reminder (the daily command didn't run, or the email failed)."""
    now = now or timezone.now()
    overdue = []
    for subscription in Subscription.objects.filter(status=Subscription.Status.ACTIVE, interval_months__gte=12):
        if not subscription.current_period_end or subscription.reminded_for == subscription.current_period_end:
            continue
        days_left = (subscription.current_period_end - now) / timedelta(days=1)
        if 0 <= days_left < REMINDER_WINDOW[0]:
            overdue.append(subscription)
    return overdue


def can_take_subscriptions():
    return payment_providers.is_configured()
