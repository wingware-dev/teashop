"""Checkout's periodic jobs (apps.jobs imports this at startup; see
docs/jobs.md).  The emails' own jobs are in emails.py."""

from apps import jobs


@jobs.job
def subscription_reminders():
    """Queue the renewal reminders due for yearly subscriptions (NY GBL
    527-a, California's automatic renewal law)."""
    from . import subscriptions

    subscriptions.send_reminders()


jobs.schedule(subscription_reminders, daily_at="14:00", tz="UTC")
