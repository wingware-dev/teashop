"""Emails to customers (order confirmation, shipped with tracking, sign-in
links, subscription notices) and new-order notices to the owner.

Plain text, honest subjects, the shop's postal address at the foot
(CAN-SPAM).  These are transactional; marketing email is phase 8.  A
failed send is logged and recorded in the audit log, and the order's
"sent at" stays empty, so the dashboard lists it to resend.
"""

import logging
import smtplib

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.audit import record

log = logging.getLogger(__name__)


def absolute(path):
    return settings.SITE_URL.rstrip("/") + path


def _send(subject, template, context, to, obj=None):
    body = render_to_string(f"checkout/email/{template}.txt", {
        "shop_name": settings.SHOP_NAME,
        "contact_email": settings.SHOP_CONTACT_EMAIL,
        "postal_address": settings.SHOP_POSTAL_ADDRESS,
        "site_url": settings.SITE_URL.rstrip("/"),
        **context,
    })
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to])
    except (smtplib.SMTPException, OSError) as exc:
        log.exception("Could not send %r to %s", subject, to)
        record("checkout.email_failed", obj=obj, message=f"{subject}: {exc}")
        return False
    record("checkout.email_sent", obj=obj, message=f"{template}: {subject}")
    return True


def order_confirmation(order):
    sent = _send(f"Your {settings.SHOP_NAME} order {order.number}", "order_confirmation",
                 {"order": order, "lines": list(order.lines.all()), "status_url": absolute(order.get_absolute_url())},
                 order.email, order)
    if sent:
        order.confirmation_sent_at = timezone.now()
        order.save(update_fields=["confirmation_sent_at"])
    return sent


def order_shipped(order):
    sent = _send(f"Your {settings.SHOP_NAME} order {order.number} is on its way", "order_shipped",
                 {"order": order, "lines": list(order.lines.all()), "status_url": absolute(order.get_absolute_url()),
                  "tracking_url": order.tracking_url()}, order.email, order)
    if sent:
        order.shipped_email_sent_at = timezone.now()
        order.save(update_fields=["shipped_email_sent_at"])
    return sent


def owner_new_order(order):
    """An email to the owner for this order now, if they chose one per
    order (OWNER_NEW_ORDER_EMAILS=each); by default new orders go in the
    6pm summary instead (fulfillment's send_order_summary)."""
    if not settings.OWNER_NOTIFY_EMAIL or settings.OWNER_NEW_ORDER_EMAILS != "each":
        return False
    from django.urls import reverse

    sent = _send(f"New order {order.number}: ${order.total:,.2f}", "owner_new_order",
                 {"order": order, "lines": list(order.lines.all()),
                  "admin_url": absolute(reverse("admin:checkout_order_change", args=[order.pk]))},
                 settings.OWNER_NOTIFY_EMAIL, order)
    if sent:
        order.owner_notified_at = timezone.now()
        order.save(update_fields=["owner_notified_at"])
    return sent


def owner_notice(subject, message, obj=None):
    """A problem the owner should hear about now (a payment that doesn't
    match, a failed renewal)."""
    if settings.OWNER_NOTIFY_EMAIL:
        return _send(subject, "owner_notice", {"message": message}, settings.OWNER_NOTIFY_EMAIL, obj)
    return False


def sign_in_link(email, url):
    return _send(f"Your {settings.SHOP_NAME} sign-in link", "sign_in_link", {"url": url, "email": email}, email)


def subscription_acknowledgment(subscription):
    """The acknowledgment NY GBL 527-a and California's law require: the
    terms, the cancellation policy and how to cancel."""
    sent = _send(f"Your {settings.SHOP_NAME} subscription: terms and how to cancel", "subscription_acknowledgment",
                 {"subscription": subscription, "cancel_url": absolute(subscription.cancel_url())},
                 subscription.email, subscription)
    if sent:
        subscription.acknowledgment_sent_at = timezone.now()
        subscription.save(update_fields=["acknowledgment_sent_at"])
    return sent


def subscription_reminder(subscription):
    from django.utils.dateformat import format as date_format

    when = date_format(timezone.localtime(subscription.current_period_end), "F j, Y")
    return _send(f"Your {settings.SHOP_NAME} subscription renews on {when}", "subscription_reminder",
                 {"subscription": subscription, "cancel_url": absolute(subscription.cancel_url())},
                 subscription.email, subscription)


def subscription_cancelled(subscription):
    return _send(f"Your {settings.SHOP_NAME} subscription is cancelled", "subscription_cancelled",
                 {"subscription": subscription}, subscription.email, subscription)


def subscription_payment_failed(subscription):
    return _send(f"Your {settings.SHOP_NAME} subscription renewal did not go through", "subscription_payment_failed",
                 {"subscription": subscription, "cancel_url": absolute(subscription.cancel_url()),
                  "card_url": absolute(subscription.card_url())},
                 subscription.email, subscription)
