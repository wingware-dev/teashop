"""Support's jobs (apps.jobs imports this at startup; see docs/jobs.md): the
assistant's run for each customer message, and reading the inbox."""

from datetime import timedelta

from django.conf import settings

from apps import jobs


@jobs.job(max_attempts=3, retry_delay=timedelta(seconds=30))
def handle_message(message_id):
    """The assistant deals with one customer message (support.agent)."""
    from . import agent

    agent.handle(message_id)


@jobs.job(max_attempts=2)
def poll_inbox():
    """Read new emails in the support mailbox, when there is one."""
    if settings.SUPPORT_INBOX != "imap":
        return
    from . import inbox

    inbox.poll()


jobs.schedule(poll_inbox, every=timedelta(minutes=settings.SUPPORT_POLL_MINUTES))
