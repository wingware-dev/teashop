"""Checkout items for the owner dashboard's "Needs your attention" list."""

from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.core.attention import Attention

from . import nexus, payments, shipping, subscriptions
from .models import CheckoutSettings, Order, Subscription


def attention_items():
    items = []
    orders_url = reverse("admin:checkout_order_changelist")
    # The fulfillment app's order queue (phase 5).
    queue_url = reverse("fulfillment:queue")
    today = timezone.localdate()
    to_ship = Order.objects.filter(status=Order.Status.PAID)
    late = to_ship.filter(ship_by__lt=today).count()
    due = to_ship.filter(ship_by__gte=today, ship_by__lte=today + timedelta(days=1)).count()
    if late:
        items.append(Attention(
            f"Orders past their promised ship date: {late}",
            "The FTC Mail Order Rule says: ship now, or tell each customer the new date and offer to cancel and "
            "refund (\"Send a delay notice\" on the order).", queue_url, "urgent"))
    if due:
        items.append(Attention(f"Orders to ship by tomorrow: {due}", "Promised ship dates are close.",
                               queue_url, "warning"))
    elif to_ship.exists():
        items.append(Attention(f"Orders to pack: {to_ship.count()}", "", queue_url, "warning"))

    unsent = Order.objects.filter(status__in=Order.PAID_STATUSES, confirmation_sent_at=None, subscription=None,
                                  paid_at__lt=timezone.now() - timedelta(minutes=10)).count()
    if unsent:
        items.append(Attention(f"Order confirmations not sent: {unsent}",
                               "Email failed.  Check the email settings, then use \"Send the confirmation email "
                               "again\" on the orders.", orders_url, "urgent"))
    mismatched = [o for o in Order.objects.filter(status=Order.Status.PAID).exclude(amount_received=None)
                  if o.amount_received != o.total]
    if mismatched:
        items.append(Attention(f"Payments that don't match the order total: {len(mismatched)}",
                               ", ".join(o.number for o in mismatched[:6]) + ".  Check them in Stripe before "
                               "shipping.", orders_url, "urgent"))
    fallback = Order.objects.filter(status__in=Order.PAID_STATUSES, tax_fallback=True,
                                    paid_at__gte=timezone.now() - timedelta(days=90))
    if fallback.exists():
        zips = sorted({o.ship_zip[:5] for o in fallback[:50]})
        items.append(Attention(f"Sales tax rates missing for {len(zips)} ZIP code{'s' if len(zips) > 1 else ''}",
                               f"Charged the highest New York rate for {', '.join(zips[:8])}.  Add their rates "
                               f"(Checkout → Tax rates).", reverse("admin:checkout_taxrate_changelist"), "warning"))
    for row in nexus.report():
        if row.needs_action:
            items.append(Attention(
                f"{row.name}: sales at {row.percent}% of its sales-tax threshold",
                f"{row.status}.  Check {row.name}'s rule; you may need to register there.",
                reverse("checkout:sales_by_state"), "urgent" if row.share >= 1 else "warning"))
    past_due = Subscription.objects.filter(status=Subscription.Status.PAST_DUE).count()
    if past_due:
        items.append(Attention(f"Subscription renewals that failed: {past_due}",
                               "Stripe retries the payment; the customer has been told.",
                               reverse("admin:checkout_subscription_changelist") + "?status__exact=past_due"))
    overdue = subscriptions.reminders_overdue()
    if overdue:
        items.append(Attention(f"Subscription renewal reminders not sent: {len(overdue)}",
                               "The law needs a reminder 15-45 days before a yearly renewal.  Is the daily "
                               "send_subscription_reminders job running?",
                               reverse("admin:checkout_subscription_changelist"), "urgent"))
    shop = CheckoutSettings.current()
    if shop.on_vacation():
        items.append(Attention("Vacation mode is on",
                               "Orders are paused." if shop.vacation_pause_orders else
                               f"Orders ship from {shop.vacation_ships_from or 'when you are back'}.",
                               reverse("admin:checkout_checkoutsettings_change", args=[shop.pk]), "warning"))
    if settings.STOREFRONT_OPEN and not (payments.is_configured() and shipping.is_configured()):
        items.append(Attention("The shop is open but checkout is not set up",
                               "Set the Stripe and EasyPost keys and the ship-from address (docs/checkout.md).",
                               "", "urgent"))
    return items
