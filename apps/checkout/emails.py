"""Emails to customers (order confirmation, shipped with tracking, sign-in
links, subscription notices) and new-order notices to the owner.

Plain text, honest subjects, the shop's postal address at the foot
(CAN-SPAM).  These are transactional; marketing email is phase 8.

Each public function (order_confirmation(order), ...) queues the email on
the job queue (apps.jobs, docs/jobs.md) and returns the Job, so a request
or webhook never waits for the mail server.  The worker sends it and
records it in the audit log; a failed send is tried again with growing
waits for about 18 hours (sign-in links: about 20 minutes), then marked
failed on the owner dashboard.  The order's "sent at" stays empty until it
is sent, so the dashboard also lists the order to resend.  The send_*
job functions send at once when called directly, raising on failure.
"""

import logging
import smtplib

from django.apps import apps as django_apps
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps import jobs
from apps.audit import record

log = logging.getLogger(__name__)

# 8 attempts: waits of 1, 4, 16 and 64 minutes, 4h16m, then 6 hours.
EMAIL_ATTEMPTS = 8
SIGN_IN_ATTEMPTS = 4


def absolute(path):
    return settings.SITE_URL.rstrip("/") + path


def send_now(subject, template, context, to, obj=None, *, app="checkout"):
    """Render {app}/email/{template}.txt and send it now; record it in the
    audit log.  Raises smtplib.SMTPException or OSError if the mail server
    refuses it (the job queue then tries again)."""
    body = render_to_string(f"{app}/email/{template}.txt", {
        "shop_name": settings.SHOP_NAME,
        "contact_email": settings.SHOP_CONTACT_EMAIL,
        "postal_address": settings.SHOP_POSTAL_ADDRESS,
        "site_url": settings.SITE_URL.rstrip("/"),
        **context,
    })
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to])
    except (smtplib.SMTPException, OSError):
        log.warning("Could not send %r to %s", subject, to)
        raise
    record(f"{app}.email_sent", obj=obj, message=f"{template}: {subject}")


def ref(obj):
    """A model instance as a job argument: [label, pk], or None."""
    return [obj._meta.label_lower, obj.pk] if obj is not None else None


def deref(value):
    """The instance ref() describes, or None if it is gone."""
    if not value:
        return None
    return django_apps.get_model(value[0]).objects.filter(pk=value[1]).first()


def _gone(what, pk):
    log.warning("%s %s no longer exists; its email is not sent", what, pk)


def _order(order_id):
    from .models import Order

    order = Order.objects.filter(pk=order_id).first()
    if order is None:
        _gone("Order", order_id)
    return order


def _subscription(subscription_id):
    from .models import Subscription

    subscription = Subscription.objects.filter(pk=subscription_id).first()
    if subscription is None:
        _gone("Subscription", subscription_id)
    return subscription


# -- Orders ------------------------------------------------------------------

def order_confirmation(order):
    return send_order_confirmation.enqueue(order.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_order_confirmation(order_id):
    if not (order := _order(order_id)):
        return
    send_now(f"Your {settings.SHOP_NAME} order {order.number}", "order_confirmation",
             {"order": order, "lines": list(order.lines.all()), "status_url": absolute(order.get_absolute_url())},
             order.email, order)
    order.confirmation_sent_at = timezone.now()
    order.save(update_fields=["confirmation_sent_at"])


def order_shipped(order):
    return send_order_shipped.enqueue(order.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_order_shipped(order_id):
    if not (order := _order(order_id)):
        return
    send_now(f"Your {settings.SHOP_NAME} order {order.number} is on its way", "order_shipped",
             {"order": order, "lines": list(order.lines.all()), "status_url": absolute(order.get_absolute_url()),
              "tracking_url": order.tracking_url()}, order.email, order)
    order.shipped_email_sent_at = timezone.now()
    order.save(update_fields=["shipped_email_sent_at"])


def owner_new_order(order):
    """An email to the owner for this order now, if they chose one per
    order (OWNER_NEW_ORDER_EMAILS=each); by default new orders go in the
    6pm summary instead (fulfillment's order_summary job).  Returns the
    Job, or False if no email is due."""
    if not settings.OWNER_NOTIFY_EMAIL or settings.OWNER_NEW_ORDER_EMAILS != "each":
        return False
    return send_owner_new_order.enqueue(order.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_owner_new_order(order_id):
    from django.urls import reverse

    if not settings.OWNER_NOTIFY_EMAIL or not (order := _order(order_id)):
        return
    send_now(f"New order {order.number}: ${order.total:,.2f}", "owner_new_order",
             {"order": order, "lines": list(order.lines.all()),
              "admin_url": absolute(reverse("admin:checkout_order_change", args=[order.pk]))},
             settings.OWNER_NOTIFY_EMAIL, order)
    order.owner_notified_at = timezone.now()
    order.save(update_fields=["owner_notified_at"])


def owner_notice(subject, message, obj=None):
    """A problem the owner should hear about now (a payment that doesn't
    match, a failed renewal).  Returns the Job, or False with no
    OWNER_NOTIFY_EMAIL."""
    if not settings.OWNER_NOTIFY_EMAIL:
        return False
    return send_owner_notice.enqueue(subject, message, ref(obj))


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_owner_notice(subject, message, obj_ref=None):
    if settings.OWNER_NOTIFY_EMAIL:
        send_now(subject, "owner_notice", {"message": message}, settings.OWNER_NOTIFY_EMAIL, deref(obj_ref))


# -- Accounts ----------------------------------------------------------------

def sign_in_link(email, url):
    return send_sign_in_link.enqueue(email, url)


@jobs.job(max_attempts=SIGN_IN_ATTEMPTS)
def send_sign_in_link(email, url):
    send_now(f"Your {settings.SHOP_NAME} sign-in link", "sign_in_link", {"url": url, "email": email}, email)


# -- Subscriptions -----------------------------------------------------------

def subscription_acknowledgment(subscription):
    """The acknowledgment NY GBL 527-a and California's law require: the
    terms, the cancellation policy and how to cancel."""
    return send_subscription_acknowledgment.enqueue(subscription.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_subscription_acknowledgment(subscription_id):
    if not (subscription := _subscription(subscription_id)):
        return
    send_now(f"Your {settings.SHOP_NAME} subscription: terms and how to cancel", "subscription_acknowledgment",
             {"subscription": subscription, "cancel_url": absolute(subscription.cancel_url())},
             subscription.email, subscription)
    subscription.acknowledgment_sent_at = timezone.now()
    subscription.save(update_fields=["acknowledgment_sent_at"])


def subscription_reminder(subscription):
    """The renewal reminder for the subscription's current period; marks
    the period reminded once sent.  Queued once per period."""
    period = subscription.current_period_end.isoformat() if subscription.current_period_end else ""
    return jobs.enqueue(send_subscription_reminder, subscription.pk,
                        key=f"subscription-reminder:{subscription.pk}:{period}")


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_subscription_reminder(subscription_id):
    from django.utils.dateformat import format as date_format

    if not (subscription := _subscription(subscription_id)):
        return
    if subscription.status != subscription.Status.ACTIVE or not subscription.current_period_end:
        log.info("Subscription %s is %s; no renewal reminder", subscription.pk, subscription.status)
        return
    if subscription.reminded_for == subscription.current_period_end:
        return  # already sent for this period
    when = date_format(timezone.localtime(subscription.current_period_end), "F j, Y")
    send_now(f"Your {settings.SHOP_NAME} subscription renews on {when}", "subscription_reminder",
             {"subscription": subscription, "cancel_url": absolute(subscription.cancel_url())},
             subscription.email, subscription)
    subscription.reminded_for = subscription.current_period_end
    subscription.save(update_fields=["reminded_for"])


def subscription_cancelled(subscription):
    return send_subscription_cancelled.enqueue(subscription.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_subscription_cancelled(subscription_id):
    if not (subscription := _subscription(subscription_id)):
        return
    send_now(f"Your {settings.SHOP_NAME} subscription is cancelled", "subscription_cancelled",
             {"subscription": subscription}, subscription.email, subscription)


def subscription_payment_failed(subscription):
    return send_subscription_payment_failed.enqueue(subscription.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_subscription_payment_failed(subscription_id):
    """With the link to the card page (Subscription.card_url) for putting
    in a new card."""
    if not (subscription := _subscription(subscription_id)):
        return
    send_now(f"Your {settings.SHOP_NAME} subscription renewal did not go through", "subscription_payment_failed",
             {"subscription": subscription, "cancel_url": absolute(subscription.cancel_url()),
              "card_url": absolute(subscription.card_url())},
             subscription.email, subscription)
