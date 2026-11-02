from django.db import models
from django.utils import timezone


class AttentionRecord(models.Model):
    """An item in the dashboard's "Needs your attention" queue: since when
    it has waited and when the owner was last reminded of it.  Kept in step
    by attention.queue(); a row goes when its item does."""

    key = models.CharField(max_length=200, unique=True)
    kind = models.CharField(max_length=30)
    title = models.CharField(max_length=300)
    first_seen = models.DateTimeField(default=timezone.now)
    reminded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["first_seen"]

    def __str__(self):
        return self.title
