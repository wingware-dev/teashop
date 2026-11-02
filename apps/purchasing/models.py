"""Stock counts: the owner counts what is really on the shelf, and the
differences from the records become stock adjustments with a reason.

A count snapshots each lot's expected quantity when it is started, so
orders packed while counting don't confuse it: the adjustment applied for
a line is (counted - expected), the difference found at the shelf.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.inventory.models import Item, Lot, StockMovement


class StockCount(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Counting"
        APPLIED = "applied", "Applied"

    started_at = models.DateTimeField(default=timezone.now)
    kinds = models.JSONField(
        default=list,
        blank=True,
        help_text="Item kinds counted; empty for everything",
    )
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN, editable=False)
    applied_at = models.DateTimeField(null=True, blank=True, editable=False)
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+", editable=False
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at", "-pk"]

    def __str__(self):
        return f"Stock count {self.pk or ''} of {self.started_at:%Y-%m-%d}".replace("  ", " ")

    def kind_labels(self):
        labels = dict(Item.Kind.choices)
        return ", ".join(labels.get(kind, kind) for kind in self.kinds) or "Everything"


class StockCountLine(models.Model):
    # Reasons a counted difference can be put down to.
    REASONS = [
        (StockMovement.Reason.COUNT, "Count correction (found more, or a recording mistake)"),
        (StockMovement.Reason.SPOILED, StockMovement.Reason.SPOILED.label),
        (StockMovement.Reason.DAMAGED, StockMovement.Reason.DAMAGED.label),
        (StockMovement.Reason.SAMPLE, StockMovement.Reason.SAMPLE.label),
        (StockMovement.Reason.MARKETING, StockMovement.Reason.MARKETING.label),
        (StockMovement.Reason.PERSONAL, StockMovement.Reason.PERSONAL.label),
        (StockMovement.Reason.UNKNOWN, StockMovement.Reason.UNKNOWN.label),
        (StockMovement.Reason.OTHER, StockMovement.Reason.OTHER.label),
    ]

    count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name="lines")
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="count_lines")
    expected = models.IntegerField(editable=False, help_text="On hand by the records when the count started")
    counted = models.PositiveIntegerField(
        null=True, blank=True, help_text="Grams (weigh bulk tea) or pieces actually there; blank if not counted"
    )
    reason = models.CharField(max_length=12, choices=REASONS, blank=True, help_text="Why it differs, if it does")
    note = models.CharField(max_length=300, blank=True)
    movement = models.OneToOneField(
        StockMovement, null=True, blank=True, on_delete=models.PROTECT, related_name="count_line", editable=False
    )

    class Meta:
        ordering = ["count", "lot__item__name", "lot__code"]
        constraints = [models.UniqueConstraint(fields=["count", "lot"], name="purchasing_count_lot_once")]

    def __str__(self):
        return f"{self.lot.code} in {self.count}"

    @property
    def difference(self):
        return None if self.counted is None else self.counted - self.expected

    def clean(self):
        difference = self.difference
        if difference and difference < 0 and not self.reason:
            raise ValidationError({"reason": "Say why it is short (choose Unknown loss if you don't know)."})
        if difference and difference > 0 and self.reason not in ("", StockMovement.Reason.COUNT, StockMovement.Reason.OTHER):
            raise ValidationError({"reason": "More than expected is a count correction (or Other)."})
