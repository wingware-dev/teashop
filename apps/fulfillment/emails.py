"""Emails from fulfillment: to customers (delay notices under the Mail
Order Rule, cancellations, refunds, part shipped, reshipped) and the
owner's daily new-order summary.  The "shipped, with tracking" email is
checkout's (orders.mark_shipped).

Like checkout's emails: plain text, the shop's address at the foot; a
failed send is logged and recorded in the audit log and returns False.
"""

import logging
import smtplib

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from apps.audit import record
from apps.checkout.emails import absolute

log = logging.getLogger(__name__)


def _send(subject, template, context, to, obj=None):
    body = render_to_string(f"fulfillment/email/{template}.txt", {
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
        record("fulfillment.email_failed", obj=obj, message=f"{subject}: {exc}")
        return False
    record("fulfillment.email_sent", obj=obj, message=f"{template}: {subject}")
    return True


def _order_context(order):
    return {"order": order, "lines": list(order.lines.all()), "status_url": absolute(order.get_absolute_url())}


def delay_notice(notice):
    order = notice.order
    return _send(f"Your {settings.SHOP_NAME} order {order.number} will ship later than promised", "delay_notice", {
        **_order_context(order), "notice": notice,
        "answer_url": absolute(reverse("fulfillment:delay_answer", args=[order.token, notice.pk])),
    }, order.email, order)


def order_cancelled(order, refund_amount, reason):
    return _send(f"Your {settings.SHOP_NAME} order {order.number} is cancelled", "order_cancelled", {
        **_order_context(order), "refund_amount": refund_amount, "reason": reason,
    }, order.email, order)


def refund_sent(refund):
    order = refund.order
    return _send(f"A refund for your {settings.SHOP_NAME} order {order.number}", "refund", {
        **_order_context(order), "refund": refund,
    }, order.email, order)


def part_shipped(order, label, rest):
    """Part of the order is on its way; rest (ParcelLines) follows."""
    return _send(f"Part of your {settings.SHOP_NAME} order {order.number} is on its way", "part_shipped", {
        **_order_context(order), "label": label, "rest": rest, "tracking_url": tracking_url(label),
    }, order.email, order)


def reshipped(order, label, reason):
    return _send(f"We have sent your {settings.SHOP_NAME} order {order.number} again", "reshipped", {
        **_order_context(order), "label": label, "reason": reason, "tracking_url": tracking_url(label),
    }, order.email, order)


def tracking_url(label):
    if label.carrier.upper() == "USPS" and label.tracking_number:
        return f"https://tools.usps.com/go/TrackConfirmAction?tLabels={label.tracking_number}"
    return ""


def owner_summary(summary):
    """The day's summary for the owner (see summary.py)."""
    if not settings.OWNER_NOTIFY_EMAIL:
        return False
    count = len(summary.new_orders)
    subject = f"{settings.SHOP_NAME}: {count} new order{'s' if count != 1 else ''}"
    if summary.late:
        subject += f", {len(summary.late)} past the promised ship date"
    return _send(subject, "owner_summary", {
        "summary": summary, "queue_url": absolute(reverse("fulfillment:queue")),
    }, settings.OWNER_NOTIFY_EMAIL)
