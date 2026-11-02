"""The reports app's scheduled jobs (apps.jobs imports this at startup; see
docs/jobs.md): the owner's reminders and the daily summary for Wave."""

import logging
from datetime import timedelta

from django.conf import settings

from apps import jobs
from apps.checkout.emails import EMAIL_ATTEMPTS

log = logging.getLogger(__name__)


@jobs.job(max_attempts=3)
def overdue_reminders():
    """Email the owner about items in "Needs your attention" past their
    deadline.  Runs every 5 minutes; the next run tries a failed send
    again, so few attempts are needed."""
    from . import reminders

    reminders.overdue()


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def daily_reminder():
    """The owner's daily list of everything waiting."""
    from . import reminders

    reminders.daily()


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def accounting_summary():
    """Post each day not yet posted to the accounting package (Wave).  A
    day Wave refuses is kept as failed and the job raises, so it is tried
    again, and fails on the dashboard after its last attempt."""
    from . import accounting

    failures = []
    for day in accounting.days_to_post():
        try:
            accounting.post_day(day)
        except accounting.AccountingError as exc:
            log.warning("Accounting summary for %s not posted: %s", day, exc)
            failures.append(f"{day}: {exc}")
    if failures:
        raise accounting.AccountingError("; ".join(failures))


jobs.schedule(overdue_reminders, every=timedelta(minutes=5))
jobs.schedule(daily_reminder, daily_at=settings.ATTENTION_DAILY_AT, tz="America/New_York")
# After midnight in New York, when the day before is complete.
jobs.schedule(accounting_summary, daily_at="02:30", tz="America/New_York")
