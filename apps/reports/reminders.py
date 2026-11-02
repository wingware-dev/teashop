"""Reminder emails for the dashboard's "Needs your attention" queue
(apps/core/attention.py).

- overdue(): every few minutes (jobs.py), one email listing the items that
  have passed their kind's deadline and not been reminded of yet: support
  escalations at once, refunds after 4 hours, broken things and failed
  jobs after an hour, approvals after 3 days...  Kinds whose deadline is
  "daily" wait for the daily reminder; orders have fulfillment's 6pm
  order summary.
- daily(): each morning (settings.ATTENTION_DAILY_AT), everything waiting,
  overdue first: low stock and items at their reorder level, purchase
  orders to approve, and the rest.

Both send through apps.checkout.emails.send_now inside their job, so a
failed send raises and the job is tried again.
"""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.checkout.emails import absolute, send_now
from apps.core import attention


def _context(entries, now):
    groups = attention.grouped(entries)
    return {
        "groups": [(kind, deadline, [(e, _link(e)) for e in group]) for kind, deadline, group in groups],
        "dashboard_url": absolute(reverse("core:owner_dashboard")),
        "now": now,
    }


def _link(entry):
    url = entry.item.url
    return absolute(url) if url.startswith("/") else url


def _mark(entries, now):
    from apps.core.models import AttentionRecord

    AttentionRecord.objects.filter(pk__in=[e.record.pk for e in entries]).update(reminded_at=now)


def due_now(entries):
    """The entries a reminder is due for: overdue, of a kind reminded here
    by time (not daily, not covered by another email), and not reminded yet."""
    return [e for e in entries if e.overdue and e.deadline.after is not None and not e.kind.reminded_by
            and e.reminded_at is None]


def overdue(now=None):
    """Send one email for the items now due a reminder; returns them."""
    if not settings.OWNER_NOTIFY_EMAIL:
        return []
    now = now or timezone.now()
    entries = due_now(attention.queue(now))
    if not entries:
        return []
    urgent = [e for e in entries if e.kind.name == "support"] or entries
    subject = (f"Waiting for you: {urgent[0].item.title}" if len(entries) == 1
               else f"Waiting for you: {len(entries)} things past their deadline")
    send_now(subject[:150], "overdue", _context(entries, now), settings.OWNER_NOTIFY_EMAIL, app="reports")
    _mark(entries, now)
    return entries


def daily(now=None):
    """The daily reminder of everything waiting; returns the entries, or
    [] when nothing waits (no email then)."""
    if not settings.OWNER_NOTIFY_EMAIL:
        return []
    now = now or timezone.now()
    entries = attention.queue(now)
    if not entries:
        return []
    late = sum(1 for e in entries if e.overdue)
    subject = f"Today's list: {len(entries)} thing{'s' if len(entries) != 1 else ''} waiting" + (
        f", {late} overdue" if late else "")
    send_now(subject, "daily", _context(entries, now), settings.OWNER_NOTIFY_EMAIL, app="reports")
    _mark([e for e in entries if e.overdue], now)
    return entries
