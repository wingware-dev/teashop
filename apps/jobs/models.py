from django.db import models
from django.utils import timezone


class Job(models.Model):
    """One call of a job function, waiting, running or finished.  Rows are
    written by enqueue() and the worker; see apps/jobs/queue.py."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Waiting"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    name = models.CharField(max_length=200, help_text="The job function's dotted path.")
    args = models.JSONField(default=list, blank=True)
    kwargs = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    # Optional: while a job with this key waits or runs, enqueueing another
    # with the same key returns it instead.
    key = models.CharField(max_length=200, blank=True, db_index=True)
    run_at = models.DateTimeField(default=timezone.now, help_text="Not run before this time.")
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    last_error = models.TextField(blank=True)
    # Who enqueued it (an apps.audit Actor), so what the job records in the
    # audit log is credited to them.
    actor = models.JSONField(default=dict, blank=True)
    locked_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "run_at"], name="jobs_job_due")]

    def __str__(self):
        return f"{self.short_name} #{self.pk}"

    @property
    def short_name(self):
        """The module and function ("emails._send_order_confirmation")."""
        return ".".join(self.name.split(".")[-2:])


class Schedule(models.Model):
    """When a periodic job (jobs.schedule()) last ran and runs next."""

    name = models.CharField(max_length=200, unique=True)
    spec = models.CharField(max_length=200, help_text="The schedule as declared; a change resets next_run_at.")
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
