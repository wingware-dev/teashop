from django.db import models
from django.utils import timezone


class AccountingEntry(models.Model):
    """One day's sales summary for the accounting package (Wave): what was
    worked out, and whether it was posted.  One per day, so a day is never
    posted twice; a correction after posting is made in Wave."""

    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        EMPTY = "empty", "Nothing to post"
        FAILED = "failed", "Not posted"

    day = models.DateField(unique=True)
    status = models.CharField(max_length=10, choices=Status.choices)
    figures = models.JSONField(default=dict, help_text="The day's totals, as strings of dollars")
    payload = models.JSONField(default=dict, blank=True, help_text="What was sent to the accounting package")
    client = models.CharField(max_length=20, help_text="wave, or fake for the stand-in")
    external_id = models.CharField(max_length=120, blank=True, help_text="The transaction's id there")
    error = models.TextField(blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-day"]
        verbose_name_plural = "accounting entries"

    def __str__(self):
        return f"Accounting summary for {self.day:%Y-%m-%d}"
