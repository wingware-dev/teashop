from decimal import Decimal

from django.db import models
from django.utils import timezone


class AIUsage(models.Model):
    """One call to the AI model by an agent, with what it cost.  The
    monthly spending cap (budget.py) adds these up."""

    agent = models.CharField(max_length=40, db_index=True)
    model = models.CharField(max_length=60)
    # The stand-in (no AI service called, nothing spent) or the live API.
    live = models.BooleanField(default=False)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal("0"))
    # What the call was for, e.g. "support:conversation:12".
    purpose = models.CharField(max_length=100, blank=True)
    at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-at", "-pk"]
        verbose_name = "AI usage"
        verbose_name_plural = "AI usage"

    def __str__(self):
        return f"{self.agent} {self.model} ${self.cost:.4f}"
