"""The ops agent on the owner dashboard's "Needs your attention" queue:

- the latest health reading's findings: urgent ones (a container down, a
  nearly full disk) as kind "problems", warnings as kind "other";
- the agent's proposals waiting for approval (kind "approvals"), and
  approved ones still to carry out;
- the quarterly security review, once the quarter's first month is over.

A health check that could not run, or upkeep that failed, shows through
apps.audit.alerts (the Operations card's kinds), not here.
"""

from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.core.attention import Attention

from . import review
from .models import Proposal, ServerReport

# Findings older than this are stale: the Operations card says the check
# is late instead.
FRESH = timedelta(hours=3)


def attention_items():
    items = []
    page = reverse("ops:owner_home")
    report = ServerReport.objects.filter(kind=ServerReport.Kind.HEALTH).first()
    if report and report.ok and timezone.now() - report.created_at < FRESH:
        for finding in report.findings:
            if finding["level"] == "info":
                continue
            urgent = finding["level"] == "urgent"
            items.append(Attention(
                f"Server: {finding['title']}", finding.get("detail", ""), page, "urgent" if urgent else "warning",
                kind="problems" if urgent else "other", key=f"ops:finding:{finding['key']}"))
    for proposal in Proposal.objects.filter(status=Proposal.Status.OPEN).order_by("created_at"):
        items.append(Attention(
            f"Server change to approve: {proposal.title}", proposal.reason[:200], proposal.get_absolute_url(),
            "warning", kind="approvals", key=f"ops:proposal:{proposal.pk}", since=proposal.created_at))
    for proposal in Proposal.objects.filter(status=Proposal.Status.APPROVED).order_by("decided_at"):
        items.append(Attention(
            f"Approved server change to carry out: {proposal.title}", "Mark it done on the server page when it is.",
            proposal.get_absolute_url(), "warning", kind="other", key=f"ops:proposal:{proposal.pk}",
            since=proposal.decided_at))
    # Only where the shop runs on its server, so a laptop isn't nagged.
    if settings.OPS_SERVER and review.due():
        today = timezone.localdate()
        items.append(Attention(
            f"Quarterly security review for {review.quarter_of(today)}", "About an hour with the checklist.",
            reverse("ops:review"), "warning", kind="other", key=f"ops:review:{review.quarter_of(today)}"))
    return items
