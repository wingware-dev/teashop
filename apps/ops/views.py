"""The owner's server page (owner/ops/): the latest health reading and its
findings, the agent's daily upkeep reports, its proposals to approve,
decline or mark done, and the quarterly security review."""

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.audit import current_actor, record
from apps.audit.ops import SUCCEEDED, record_ops_event
from apps.core.decorators import owner_required

from . import jobs, review
from .models import Proposal, QuarterlyReview, ServerReport

DECISIONS = {
    "approve": (Proposal.Status.OPEN, Proposal.Status.APPROVED, "Approved: carry it out, then mark it done."),
    "decline": (Proposal.Status.OPEN, Proposal.Status.DECLINED, "Declined.  The agent won't propose it again for "
                                                                "30 days."),
    "done": (Proposal.Status.APPROVED, Proposal.Status.DONE, "Marked done.  The next health check confirms it."),
}


@never_cache
@owner_required
def owner_home(request):
    health = ServerReport.objects.filter(kind=ServerReport.Kind.HEALTH).first()
    upkeep = ServerReport.objects.filter(kind=ServerReport.Kind.UPKEEP)[:14]
    return render(request, "ops/owner_home.html", {
        "server_on": bool(settings.OPS_SERVER),
        "demo": settings.OPS_SERVER == "demo",
        "health": health,
        "reading": health.data if health else {},
        "upkeep": upkeep,
        "open_proposals": Proposal.objects.filter(status=Proposal.Status.OPEN).order_by("created_at"),
        "approved_proposals": Proposal.objects.filter(status=Proposal.Status.APPROVED).order_by("decided_at"),
        "past_proposals": Proposal.objects.filter(status__in=[Proposal.Status.DONE, Proposal.Status.DECLINED])[:10],
        "review": review.current_review(),
        "review_due": review.due(),
        "quarter": review.quarter_of(timezone.localdate()),
    })


@owner_required
@require_POST
def check_now(request):
    if not settings.OPS_SERVER:
        messages.error(request, "Server checks are off on this computer (OPS_SERVER is empty).")
    else:
        jobs.check_health.enqueue()
        messages.success(request, "Checking the server: the reading appears here in a minute.")
    return redirect("ops:owner_home")


@owner_required
@require_POST
def decide(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    action = request.POST.get("action", "")
    if action not in DECISIONS:
        messages.error(request, "Unknown choice.")
        return redirect(proposal.get_absolute_url())
    allowed_from, to, done_message = DECISIONS[action]
    if proposal.status != allowed_from:
        messages.error(request, f"This proposal is already {proposal.get_status_display().lower()}.")
        return redirect(proposal.get_absolute_url())
    proposal.status = to
    proposal.note = (request.POST.get("note", "").strip()[:2000]) or proposal.note
    if action != "done":
        proposal.decided_at = timezone.now()
        proposal.decided_by = request.user
    proposal.save()
    record(f"ops.proposal_{to}", obj=proposal, message=proposal.title)
    messages.success(request, done_message)
    return redirect(proposal.get_absolute_url())


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def review_page(request):
    today = timezone.localdate()
    quarter = review.quarter_of(today)
    done = review.current_review(today)
    facts = review.facts(today)
    checked, notes, error = [], "", ""
    if request.method == "POST" and not done:
        checked = [key for key in request.POST.getlist("item") if key in review.KEYS]
        notes = request.POST.get("notes", "").strip()[:5000]
        if len(checked) < len(review.KEYS) and not notes:
            error = "Tick each item, or say in the notes why one was skipped."
        else:
            done = QuarterlyReview.objects.create(
                quarter=quarter, completed_by=request.user, checked=checked, notes=notes,
                facts={key: [[ok, text] for ok, text in value] for key, value in facts.items()})
            skipped = len(review.KEYS) - len(checked)
            record_ops_event("quarterly_review", SUCCEEDED, actor=current_actor(),
                             message=f"Security review {quarter} done" +
                             (f"; {skipped} item{'s' if skipped != 1 else ''} skipped" if skipped else ""))
            messages.success(request, f"The {quarter} security review is recorded.  Thank you.")
            return redirect(reverse("ops:review"))
    items = [{"key": key, "title": title, "how": how, "facts": facts.get(key, []),
              "checked": key in (done.checked if done else checked)} for key, title, how in review.ITEMS]
    return render(request, "ops/review.html", {
        "quarter": quarter, "done": done, "items": items, "notes": notes, "error": error,
        "past": QuarterlyReview.objects.exclude(quarter=quarter)[:8],
    })
