"""The ops agent's schedules (apps.jobs imports this at startup; see
docs/jobs.md): the hourly health check and the daily upkeep.  Both do
nothing while OPS_SERVER is empty (a laptop)."""

from datetime import timedelta

from django.conf import settings

from apps import jobs


@jobs.job(max_attempts=1)
def check_health():
    """Read and assess the server (agent.check_health).  A failure is the
    finding itself, recorded on the dashboard, so it is not retried."""
    from . import agent

    agent.check_health()


@jobs.job(max_attempts=2, retry_delay=timedelta(minutes=30))
def daily_upkeep():
    """Security updates, logs, proposals and the day's report (agent.upkeep)."""
    from . import agent

    agent.upkeep()


jobs.schedule(check_health, every=timedelta(minutes=settings.OPS_HEALTH_EVERY_MINUTES))
jobs.schedule(daily_upkeep, daily_at=settings.OPS_UPKEEP_AT)
