"""Reports items for the owner dashboard: days the accounting summary
could not be posted to Wave."""

from django.urls import reverse

from apps.core.attention import Attention

from .models import AccountingEntry


def attention_items():
    failed = list(AccountingEntry.objects.filter(status=AccountingEntry.Status.FAILED).order_by("day"))
    if not failed:
        return []
    days = ", ".join(f"{entry.day:%b %-d}" for entry in failed[:6]) + (" ..." if len(failed) > 6 else "")
    return [Attention(
        f"Daily summaries not sent to Wave: {len(failed)}",
        f"{days}.  {failed[-1].error[:200]}  They are tried again each night.",
        reverse("reports:accounting"), "warning", kind="jobs", key="reports:wave-failed",
        since=failed[0].created_at)]
