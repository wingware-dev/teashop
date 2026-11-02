"""The owner's daily new-order summary (at 6pm, by the order_summary job in
jobs.py): new orders since the last one, and what the Mail Order Rule
needs."""

from dataclasses import dataclass, field
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.checkout.models import Order

from . import emails
from .services import consent_overdue
from .models import DelayNotice


class SummaryNotSent(Exception):
    pass


@dataclass
class Summary:
    new_orders: list = field(default_factory=list)
    to_pack: list = field(default_factory=list)
    late: list = field(default_factory=list)
    due: list = field(default_factory=list)
    awaiting_consent: list = field(default_factory=list)
    consent_overdue: list = field(default_factory=list)

    @property
    def worth_sending(self):
        return bool(self.new_orders or self.late or self.due or self.awaiting_consent)


def build(day=None):
    day = day or timezone.localdate()
    to_pack = list(Order.objects.filter(status=Order.Status.PAID).order_by("ship_by", "paid_at"))
    return Summary(
        new_orders=[order for order in to_pack if order.owner_notified_at is None],
        to_pack=to_pack,
        late=[order for order in to_pack if order.ship_by and order.ship_by < day],
        due=[order for order in to_pack if order.ship_by and day <= order.ship_by <= day + timedelta(days=1)],
        awaiting_consent=list(DelayNotice.objects.filter(
            needs_consent=True, response=DelayNotice.Response.WAITING, order__status=Order.Status.PAID)
            .select_related("order")),
        consent_overdue=list(consent_overdue(day)),
    )


def send(day=None):
    """Send the summary if there is anything in it; mark the new orders as
    told.  Returns the Summary, or None if there was nothing to send.
    Raises SummaryNotSent if the email failed."""
    summary = build(day)
    if not summary.worth_sending:
        return None
    if not emails.owner_summary(summary):
        raise SummaryNotSent("The order summary email could not be sent (see the log).")
    with transaction.atomic():
        Order.objects.filter(pk__in=[order.pk for order in summary.new_orders]).update(owner_notified_at=timezone.now())
    return summary
