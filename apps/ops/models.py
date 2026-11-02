from django.conf import settings
from django.db import models
from django.urls import reverse


class ServerReport(models.Model):
    """One reading or upkeep run: an hourly health check, or the agent's
    daily upkeep with what it did.  `data` keeps the server's JSON;
    `findings` the assessment (findings.Finding.as_dict())."""

    class Kind(models.TextChoices):
        HEALTH = "health", "Health check"
        UPKEEP = "upkeep", "Daily upkeep"

    kind = models.CharField(max_length=10, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # False when the server could not be reached or a step failed.
    ok = models.BooleanField(default=True)
    summary = models.CharField(max_length=500)
    findings = models.JSONField(default=list, blank=True)
    # Upkeep: the actions taken, each {"action", "ok", "detail"}.
    actions = models.JSONField(default=list, blank=True)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.get_kind_display()} {self.created_at:%Y-%m-%d %H:%M}: {self.summary}"

    def serious_findings(self):
        return [finding for finding in self.findings if finding.get("level") != "info"]


class Proposal(models.Model):
    """A change the ops agent may not make itself, for the owner to approve
    and carry out (a restart, a bigger disk, an Ubuntu upgrade)."""

    class Status(models.TextChoices):
        OPEN = "open", "Waiting for you"
        APPROVED = "approved", "Approved, to do"
        DONE = "done", "Done"
        DECLINED = "declined", "Declined"

    class Risk(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    key = models.CharField(max_length=200, db_index=True)
    title = models.CharField(max_length=300)
    reason = models.TextField()
    steps = models.TextField()
    risk = models.CharField(max_length=10, choices=Risk.choices, default=Risk.LOW)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True)
    proposed_by = models.CharField(max_length=60)
    # True when the agent had read the server's logs (text from outside the
    # shop) before proposing: check its steps with extra care.
    after_reading_logs = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="+")
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("ops:owner_home") + f"#proposal-{self.pk}"

    @property
    def is_active(self):
        return self.status in (self.Status.OPEN, self.Status.APPROVED)


class QuarterlyReview(models.Model):
    """The owner's quarterly security review (review.py's checklist)."""

    quarter = models.CharField(max_length=7, unique=True)  # "2026-Q4"
    completed_at = models.DateTimeField(auto_now_add=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                     related_name="+")
    checked = models.JSONField(default=list)  # the keys of the items ticked
    # What the automatic checks said when it was done.
    facts = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-quarter"]

    def __str__(self):
        return f"Security review {self.quarter}"
