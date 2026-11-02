"""Support on the owner dashboard's "Needs your attention" queue, as kind
"support" (a reminder email at once): conversations handed to the owner,
drafts to check, and messages the assistant hasn't dealt with.  Also a
nudge when a category is ready to be answered alone."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.core.attention import Attention

from . import services
from .models import ANSWERABLE, CategoryMode, Conversation, Message

STUCK_AFTER = timedelta(minutes=10)


def _about(conversation):
    first = conversation.messages.filter(sender=Message.Sender.CUSTOMER).first()
    text = conversation.subject or (first.body if first else "")
    text = " ".join(text.split())
    return text[:60] + ("..." if len(text) > 60 else "")


def attention_items():
    items = []
    for conversation in Conversation.objects.filter(status=Conversation.Status.ESCALATED).order_by("escalated_at"):
        items.append(Attention(
            f"Customer waiting for you: {conversation.email}",
            f"\"{_about(conversation)}\" ({conversation.get_channel_display().lower()}).  "
            f"{conversation.escalation_reason}", conversation.get_absolute_url(), "urgent",
            kind="support", key=f"support:conversation:{conversation.pk}",
            since=conversation.escalated_at or conversation.last_activity_at))
    for conversation in Conversation.objects.filter(status=Conversation.Status.DRAFTED).order_by("last_activity_at"):
        draft = conversation.pending_draft()
        items.append(Attention(
            f"Reply to check and send: {conversation.email}",
            f"\"{_about(conversation)}\".  The assistant drafted an answer ({draft.get_category_display().lower()})"
            if draft else f"\"{_about(conversation)}\"", conversation.get_absolute_url(), "warning",
            kind="support", key=f"support:conversation:{conversation.pk}",
            since=draft.created_at if draft else conversation.last_activity_at))
    stuck = Message.objects.filter(sender=Message.Sender.CUSTOMER, handled_at=None,
                                   created_at__lt=timezone.now() - STUCK_AFTER)
    if stuck.exists():
        items.append(Attention(
            f"Customer messages the assistant hasn't answered: {stuck.count()}",
            "Check that the worker is running and look for failed jobs (Background jobs); answer them yourself "
            "meanwhile.", reverse("support:owner_inbox"), "urgent", kind="support", key="support:stuck",
            since=stuck.order_by("created_at").first().created_at))
    alone = set(CategoryMode.objects.filter(answers_alone=True).values_list("category", flat=True))
    for category in ANSWERABLE:
        if category not in alone and services.readiness(category)["ready"]:
            items.append(Attention(
                f"The assistant is ready to answer \"{category.label}\" alone",
                "Its recent drafts went out with no or small edits.  You can let it answer these itself.",
                reverse("support:owner_inbox"), "warning", kind="other", key=f"support:ready:{category}"))
    return items
