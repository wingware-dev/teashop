"""The email list's daily send (apps.jobs imports this at startup; see
docs/jobs.md).  Approving a mailing also queues a send at once."""

from django.conf import settings

from apps import jobs


@jobs.job
def dispatch_due():
    """Queue an email for each subscriber who is due one and has approved
    mailings waiting (one job per email)."""
    from . import services

    services.dispatch()


jobs.schedule(dispatch_due, daily_at=settings.EMAIL_LIST_SEND_AT)
