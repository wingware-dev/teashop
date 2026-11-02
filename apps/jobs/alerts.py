"""Job items for the owner dashboard's "Needs your attention" list."""

from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.core.attention import Attention

from .models import Job

# A job waiting this long past its time means no worker is taking jobs.
WORKER_LATE = timedelta(minutes=10)


def attention_items():
    items = []
    changelist = reverse("admin:jobs_job_changelist")
    failed = Job.objects.filter(status=Job.Status.FAILED)
    if failed.exists():
        names = sorted({job.short_name for job in failed[:50]})
        items.append(Attention(
            f"Background jobs that failed: {failed.count()}",
            f"{', '.join(names[:5])}.  Each was tried several times.  Fix the cause (for an email, the email "
            "settings), then use \"Run again\" on them.", changelist + "?status__exact=failed", "urgent",
            kind="jobs", key="jobs:failed",
            since=failed.order_by("finished_at").values_list("finished_at", flat=True).first()))
    if not settings.JOBS_EAGER:
        late = Job.objects.filter(status=Job.Status.QUEUED, run_at__lt=timezone.now() - WORKER_LATE)
        if late.exists():
            items.append(Attention(
                f"Background jobs are not running: {late.count()} waiting",
                "Emails and daily jobs wait for the job worker.  On the server: docker compose up -d worker, "
                "then docker compose logs worker (docs/jobs.md).", changelist + "?status__exact=queued", "urgent",
                kind="jobs", key="jobs:not-running"))
    return items
