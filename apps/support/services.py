"""Support conversations: what customers send, what the assistant and the
owner send back, drafts and the watch-mode approval rate.

Every step is recorded in the audit log ("support.*"), credited to whoever
did it: the customer's request, the support agent (inside its run), or the
signed-in owner.
"""

import difflib
import re

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps import jobs
from apps.audit import agent_involved, record

from .models import ANSWERABLE, CategoryMode, Conversation, Draft, Message

MAX_MESSAGE_CHARS = 4000
# Customer messages in one chat before it must continue by email.
MAX_CHAT_MESSAGES = 40
# Sent with no more than small edits: counts towards the approval rate.
APPROVED_SIMILARITY = 0.9


def hold_text(conversation):
    where = "here and by email" if conversation.channel == Conversation.Channel.CHAT else "by email"
    return (f"Thanks for writing.  This one needs a person at the shop, so I've passed it on, and we'll get back "
            f"to you {where} as soon as we can.")


def acknowledge_text(conversation):
    return ("Thanks!  I've got your question.  A person at the shop checks my answers at the moment, so the "
            "reply will come here and by email shortly.")


# -- Customers -------------------------------------------------------------------

def _clean_body(body):
    body = (body or "").replace("\r\n", "\n").strip()
    if not body:
        raise ValidationError("Write a message.")
    return body[:MAX_MESSAGE_CHARS]


def start_chat(email, name, body):
    conversation = Conversation.objects.create(channel=Conversation.Channel.CHAT, email=email.strip().lower(),
                                               name=name.strip()[:100])
    record("support.chat_started", obj=conversation)
    add_customer_message(conversation, body)
    return conversation


def add_customer_message(conversation, body, *, email_message_id="", subject=""):
    """Keep a customer's message and queue the assistant for it."""
    if conversation.channel == Conversation.Channel.CHAT and conversation.messages.filter(
            sender=Message.Sender.CUSTOMER).count() >= MAX_CHAT_MESSAGES:
        raise ValidationError(f"This chat is full.  Please write to {settings.SUPPORT_EMAIL} to go on.")
    message = Message.objects.create(conversation=conversation, sender=Message.Sender.CUSTOMER,
                                     body=_clean_body(body), email_message_id=email_message_id[:250])
    fields = ["last_activity_at"]
    conversation.last_activity_at = message.created_at
    if conversation.status in (Conversation.Status.ANSWERED, Conversation.Status.CLOSED):
        conversation.status = Conversation.Status.OPEN
        fields.append("status")
    if subject and not conversation.subject:
        conversation.subject = subject[:200]
        fields.append("subject")
    conversation.save(update_fields=fields)
    record("support.message_received", obj=conversation, message=f"{conversation.channel}, {len(message.body)} "
           "characters")
    from .jobs import handle_message

    handle_message.enqueue(message.pk)
    return message


# -- Sending -----------------------------------------------------------------------

def _post(conversation, sender, body):
    message = Message.objects.create(conversation=conversation, sender=sender, body=body.strip())
    conversation.last_activity_at = message.created_at
    conversation.save(update_fields=["last_activity_at"])
    emailed = conversation.channel == Conversation.Channel.EMAIL or sender == Message.Sender.OWNER
    if emailed:
        from .emails import send_reply

        send_reply.enqueue(message.pk)
    return message


def remind_owner_now():
    """Run the dashboard's overdue reminders now rather than in up to five
    minutes, so a support item reaches the owner at once."""
    from apps.reports.jobs import overdue_reminders

    jobs.enqueue(overdue_reminders, key="support:remind-now")


def escalate(conversation, reason):
    """Hand the conversation to the owner, telling the customer once."""
    first = conversation.status != Conversation.Status.ESCALATED
    conversation.status = Conversation.Status.ESCALATED
    conversation.escalated_at = conversation.escalated_at if not first else timezone.now()
    conversation.escalation_reason = reason[:300]
    conversation.save(update_fields=["status", "escalated_at", "escalation_reason"])
    record("support.escalated", obj=conversation, message=reason)
    if first:
        _post(conversation, Message.Sender.AGENT, hold_text(conversation))
        remind_owner_now()


def _replace_pending(conversation):
    conversation.drafts.filter(status=Draft.Status.PENDING).update(status=Draft.Status.REPLACED,
                                                                   decided_at=timezone.now())


def make_draft(conversation, category, text, *, acknowledge=False):
    """Watch mode: keep the assistant's answer for the owner to check."""
    _replace_pending(conversation)
    draft = Draft.objects.create(conversation=conversation, category=category, body=text)
    conversation.category = category
    if conversation.status != Conversation.Status.ESCALATED:
        conversation.status = Conversation.Status.DRAFTED
    conversation.save(update_fields=["category", "status"])
    record("support.drafted", obj=conversation, message=f"{category.label}")
    if acknowledge:
        if conversation.channel == Conversation.Channel.CHAT:
            _post(conversation, Message.Sender.AGENT, acknowledge_text(conversation))
        remind_owner_now()
    return draft


def agent_answer(conversation, category, text):
    """The assistant answers on its own (a category the owner let it)."""
    message = _post(conversation, Message.Sender.AGENT, text)
    conversation.category = category
    conversation.status = Conversation.Status.ANSWERED
    conversation.save(update_fields=["category", "status"])
    record("support.answered_alone", obj=conversation, message=f"{category.label}")
    return message


# -- The owner ---------------------------------------------------------------------

def similarity(draft, sent):
    """How close sent is to draft, word by word (1.0: the same)."""
    a, b = re.findall(r"\S+", draft.lower()), re.findall(r"\S+", sent.lower())
    return round(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), 3)


def owner_reply(conversation, body, draft=None):
    """The owner sends a reply (a draft, edited or not, or their own)."""
    body = _clean_body(body)
    if draft is not None:
        if draft.conversation_id != conversation.pk or draft.status != Draft.Status.PENDING:
            raise ValidationError("That draft was already dealt with.")
        draft.sent_body = body
        draft.similarity = similarity(draft.body, body)
        draft.approved = draft.similarity >= APPROVED_SIMILARITY
        draft.status = Draft.Status.SENT
        draft.decided_at = timezone.now()
        draft.save(update_fields=["sent_body", "similarity", "approved", "status", "decided_at"])
    else:
        _replace_pending(conversation)
    message = _post(conversation, Message.Sender.OWNER, body)
    conversation.status = Conversation.Status.ANSWERED
    conversation.escalated_at = None
    conversation.save(update_fields=["status", "escalated_at"])
    record("support.owner_replied", obj=conversation,
           message=f"draft {'unchanged' if draft and draft.similarity == 1 else 'edited' if draft else 'not used'}")
    return message


def discard_draft(draft):
    draft.status = Draft.Status.DISCARDED
    draft.approved = False
    draft.decided_at = timezone.now()
    draft.save(update_fields=["status", "approved", "decided_at"])
    conversation = draft.conversation
    if conversation.status == Conversation.Status.DRAFTED:
        conversation.status = Conversation.Status.ESCALATED
        conversation.escalated_at = conversation.escalated_at or draft.created_at
        conversation.escalation_reason = "You discarded the assistant's draft"
        conversation.save(update_fields=["status", "escalated_at", "escalation_reason"])
    record("support.draft_discarded", obj=conversation)


def close(conversation):
    _replace_pending(conversation)
    conversation.status = Conversation.Status.CLOSED
    conversation.escalated_at = None
    conversation.save(update_fields=["status", "escalated_at"])
    record("support.closed", obj=conversation)


# -- Watch mode and answering alone ----------------------------------------------

def readiness(category):
    """How the latest decided drafts in category went: {decided, approved,
    rate, ready, needed}."""
    decided = list(Draft.objects.filter(category=category, status__in=[Draft.Status.SENT, Draft.Status.DISCARDED])
                   .order_by("-decided_at").values_list("approved", flat=True)[:settings.SUPPORT_READY_MIN_DRAFTS])
    approved = sum(1 for value in decided if value)
    rate = approved / len(decided) if decided else None
    ready = len(decided) >= settings.SUPPORT_READY_MIN_DRAFTS and rate >= settings.SUPPORT_READY_RATE
    return {"decided": len(decided), "approved": approved, "rate": rate, "ready": ready,
            "needed": max(settings.SUPPORT_READY_MIN_DRAFTS - len(decided), 0)}


def set_answers_alone(category, on):
    """The owner lets the assistant answer category alone, or not.  Turning
    it on needs the approval rate to show it is ready; never for Other, and
    never by an agent."""
    if agent_involved():
        raise PermissionDenied("AI agents cannot change what they may answer alone.")
    if on and category not in ANSWERABLE:
        raise ValidationError("The assistant never answers this category alone.")
    if on and not readiness(category)["ready"]:
        raise ValidationError("Not ready yet: the approval rate needs more drafts sent unchanged.")
    mode, _ = CategoryMode.objects.get_or_create(category=category)
    mode.answers_alone = on
    mode.changed_at = timezone.now()
    mode.save(update_fields=["answers_alone", "changed_at"])
    record("support.mode_changed", obj=mode, message=str(mode))
    return mode
