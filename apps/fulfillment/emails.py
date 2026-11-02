"""Emails from fulfillment: to customers (delay notices under the Mail
Order Rule, cancellations, refunds, part shipped, reshipped) and the
owner's daily new-order summary.  The "shipped, with tracking" email is
checkout's (orders.mark_shipped).

Like checkout's emails: plain text, the shop's address at the foot, and
each customer email is queued on the job queue (docs/jobs.md), which
sends it, records it in the audit log and retries a failure.  The public
functions keep their arguments and return the Job.  owner_summary() sends
at once: it runs inside the daily order_summary job, which is retried.
"""

import logging
import smtplib
from decimal import Decimal

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps import jobs
from apps.checkout.emails import EMAIL_ATTEMPTS, absolute, send_now

log = logging.getLogger(__name__)


def _send(subject, template, context, to, obj=None):
    send_now(subject, template, context, to, obj, app="fulfillment")


def _order_context(order):
    return {"order": order, "lines": list(order.lines.all()), "status_url": absolute(order.get_absolute_url())}


def _get(model, pk):
    found = model.objects.filter(pk=pk).first()
    if found is None:
        log.warning("%s %s no longer exists; its email is not sent", model.__name__, pk)
    return found


def _order(order_id):
    from apps.checkout.models import Order

    return _get(Order, order_id)


def _label(label_id):
    from .models import PostageLabel

    return _get(PostageLabel, label_id)


def delay_notice(notice):
    """The Mail Order Rule's notice of a new ship date; sets the notice's
    sent_at once sent."""
    return send_delay_notice.enqueue(notice.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_delay_notice(notice_id):
    from .models import DelayNotice

    if not (notice := _get(DelayNotice, notice_id)):
        return
    order = notice.order
    _send(f"Your {settings.SHOP_NAME} order {order.number} will ship later than promised", "delay_notice", {
        **_order_context(order), "notice": notice,
        "answer_url": absolute(reverse("fulfillment:delay_answer", args=[order.token, notice.pk])),
    }, order.email, order)
    notice.sent_at = timezone.now()
    notice.save(update_fields=["sent_at"])


def order_cancelled(order, refund_amount, reason):
    return send_order_cancelled.enqueue(order.pk, str(refund_amount), reason)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_order_cancelled(order_id, refund_amount, reason):
    if not (order := _order(order_id)):
        return
    _send(f"Your {settings.SHOP_NAME} order {order.number} is cancelled", "order_cancelled", {
        **_order_context(order), "refund_amount": Decimal(refund_amount), "reason": reason,
    }, order.email, order)


def refund_sent(refund):
    """Tells the customer about a refund; sets the refund's email_sent_at
    once sent."""
    return send_refund.enqueue(refund.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_refund(refund_id):
    from .models import Refund

    if not (refund := _get(Refund, refund_id)):
        return
    order = refund.order
    _send(f"A refund for your {settings.SHOP_NAME} order {order.number}", "refund", {
        **_order_context(order), "refund": refund,
    }, order.email, order)
    refund.email_sent_at = timezone.now()
    refund.save(update_fields=["email_sent_at"])


def part_shipped(order, label, rest):
    """Part of the order is on its way; rest (ParcelLines) follows."""
    return send_part_shipped.enqueue(order.pk, label.pk, [line.pk for line in rest])


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_part_shipped(order_id, label_id, rest_ids):
    from .models import ParcelLine

    if not (order := _order(order_id)) or not (label := _label(label_id)):
        return
    found = ParcelLine.objects.select_related("order_line").in_bulk(rest_ids)
    rest = [found[pk] for pk in rest_ids if pk in found]
    _send(f"Part of your {settings.SHOP_NAME} order {order.number} is on its way", "part_shipped", {
        **_order_context(order), "label": label, "rest": rest, "tracking_url": tracking_url(label),
    }, order.email, order)


def reshipped(order, label, reason):
    return send_reshipped.enqueue(order.pk, label.pk, reason)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_reshipped(order_id, label_id, reason):
    if not (order := _order(order_id)) or not (label := _label(label_id)):
        return
    _send(f"We have sent your {settings.SHOP_NAME} order {order.number} again", "reshipped", {
        **_order_context(order), "label": label, "reason": reason, "tracking_url": tracking_url(label),
    }, order.email, order)


def tracking_url(label):
    if label.carrier.upper() == "USPS" and label.tracking_number:
        return f"https://tools.usps.com/go/TrackConfirmAction?tLabels={label.tracking_number}"
    return ""


def owner_summary(summary):
    """Send the day's summary for the owner now (see summary.py).  Returns
    False if there is no OWNER_NOTIFY_EMAIL or the send failed."""
    if not settings.OWNER_NOTIFY_EMAIL:
        return False
    count = len(summary.new_orders)
    subject = f"{settings.SHOP_NAME}: {count} new order{'s' if count != 1 else ''}"
    if summary.late:
        subject += f", {len(summary.late)} past the promised ship date"
    try:
        _send(subject, "owner_summary", {
            "summary": summary, "queue_url": absolute(reverse("fulfillment:queue")),
        }, settings.OWNER_NOTIFY_EMAIL)
    except (smtplib.SMTPException, OSError):
        log.exception("Could not send the order summary")
        return False
    return True
