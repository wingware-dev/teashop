"""Fulfillment's periodic jobs (apps.jobs imports this at startup; see
docs/jobs.md).  The emails' own jobs are in emails.py."""

from django.conf import settings

from apps import jobs
from apps.checkout.emails import EMAIL_ATTEMPTS


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def order_summary():
    """The owner's 6pm summary of new orders and what the FTC Mail Order
    Rule needs.  A failed email raises SummaryNotSent, so it is retried."""
    from . import summary

    if settings.OWNER_NOTIFY_EMAIL:
        summary.send()


jobs.schedule(order_summary, daily_at="18:00", tz="America/New_York")
