"""Stripe's webhook: Stripe tells the shop when a payment succeeds, a
subscription renews or fails, or a subscription changes.

Each event is checked against STRIPE_WEBHOOK_SECRET and handled once
(WebhookEvent).  An event that fails to be handled answers 500, so Stripe
sends it again later.  In Stripe's dashboard, send these events to
/checkout/stripe-webhook/: payment_intent.succeeded, invoice.paid,
invoice.payment_failed, setup_intent.succeeded (a new card from the
subscription card page), customer.subscription.updated and
customer.subscription.deleted.
"""

import logging
from datetime import datetime
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import payments, subscriptions
from .models import Order, Subscription, WebhookEvent
from .orders import mark_paid

log = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    try:
        # Plain dicts from here on: Stripe's objects are not dicts.
        event = payments.parse_event(request.body, request.META.get("HTTP_STRIPE_SIGNATURE", "")).to_dict()
    except payments.PaymentError as exc:
        log.warning("%s", exc)
        return HttpResponse(status=400)
    if WebhookEvent.objects.filter(event_id=event["id"]).exists():
        return HttpResponse("Already handled")
    handle(event)
    WebhookEvent.objects.get_or_create(event_id=event["id"], defaults={"type": event["type"]})
    return HttpResponse("OK")


def _invoice_subscription_id(invoice):
    """The subscription an invoice bills: under parent.subscription_details
    in recent API versions, a top-level field in older ones."""
    parent = invoice.get("parent") or {}
    details = parent.get("subscription_details") or {}
    found = details.get("subscription") or invoice.get("subscription")
    return found if isinstance(found, str) else (found or {}).get("id", "")


def _invoice_period_end(invoice):
    lines = (invoice.get("lines") or {}).get("data") or []
    end = (lines[0].get("period") or {}).get("end") if lines else None
    return datetime.fromtimestamp(end, tz=dt_timezone.utc) if end else None


def handle(event):
    kind = event["type"]
    obj = event["data"]["object"]
    if kind == "payment_intent.succeeded":
        order = Order.objects.filter(payment_id=obj["id"]).first()
        if order is None:
            number = (obj.get("metadata") or {}).get("order_number", "")
            order = Order.objects.filter(number=number).first() if number else None
        if order is None:
            # Subscription invoices are paid through PaymentIntents too.
            log.info("PaymentIntent %s is not for a shop order", obj["id"])
            return
        mark_paid(order, Decimal(obj.get("amount_received") or 0) / 100)
    elif kind in ("invoice.paid", "invoice.payment_failed"):
        subscription_id = _invoice_subscription_id(obj)
        subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).first() \
            if subscription_id else None
        if subscription is None:
            log.info("Invoice %s is not for a shop subscription", obj.get("id"))
            return
        if kind == "invoice.paid":
            subscriptions.record_payment(
                subscription, first=obj.get("billing_reason") == "subscription_create",
                period_end=_invoice_period_end(obj), invoice_id=obj["id"],
                amount=Decimal(obj.get("amount_paid") or 0) / 100)
        else:
            subscriptions.payment_failed(subscription)
    elif kind == "setup_intent.succeeded":
        # A new card from the card page, in case the customer never got back
        # to the return page (which does the same, so this is often a repeat).
        metadata = obj.get("metadata") or {}
        subscription = Subscription.objects.filter(pk=metadata.get("subscription")).first() \
            if metadata.get("purpose") == "card_update" and str(metadata.get("subscription", "")).isdigit() else None
        if subscription is None or not subscriptions.can_update_card(subscription):
            log.info("SetupIntent %s is not a card change for a live subscription", obj.get("id"))
            return
        subscriptions.update_card(subscription, obj["id"])
    elif kind in ("customer.subscription.updated", "customer.subscription.deleted"):
        subscription = Subscription.objects.filter(stripe_subscription_id=obj["id"]).first()
        if subscription:
            subscriptions.sync_from_stripe(subscription, obj)
    else:
        log.info("Ignoring Stripe event %s", kind)
