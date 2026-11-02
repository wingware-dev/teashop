"""Support replies by email, on the job queue (docs/jobs.md).

Each outgoing message in an email conversation is emailed, and so is each
owner reply in a chat (the customer may have left the page).  Replies come
from SUPPORT_EMAIL and thread under the customer's email (In-Reply-To and
References).  An email the assistant sent on its own starts with the AI
disclosure (apps.agents.labels) and says Auto-Submitted: auto-replied, so
other robots don't answer it back.
"""

import logging
import smtplib
from email.utils import formataddr, make_msgid, parseaddr

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from apps import jobs
from apps.agents.labels import label_email
from apps.audit import record
from apps.checkout.emails import EMAIL_ATTEMPTS, absolute

from .models import Conversation, Message

log = logging.getLogger(__name__)


def subject_for(conversation):
    subject = conversation.subject or f"Your question to {settings.SHOP_NAME}"
    return subject if subject.lower().startswith("re:") else f"Re: {subject}"


def _thread_headers(conversation, message):
    ids = list(conversation.messages.filter(pk__lt=message.pk).exclude(email_message_id="")
               .order_by("pk").values_list("email_message_id", flat=True))
    if not ids:
        return {}
    return {"In-Reply-To": ids[-1], "References": " ".join(ids[-10:])}


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_reply(message_id):
    message = Message.objects.select_related("conversation").filter(pk=message_id).first()
    if message is None:
        log.warning("Support message %s no longer exists; its email is not sent", message_id)
        return
    if message.emailed_at:
        return
    conversation = message.conversation
    body = label_email(message.body) if message.is_ai else message.body.strip()
    text = render_to_string("support/email/reply.txt", {
        "body": body, "conversation": conversation, "shop_name": settings.SHOP_NAME,
        "postal_address": settings.SHOP_POSTAL_ADDRESS, "support_email": settings.SUPPORT_EMAIL,
        "chat_url": absolute(conversation.chat_url()) if conversation.channel == Conversation.Channel.CHAT else "",
    })
    domain = parseaddr(settings.SUPPORT_EMAIL)[1].rpartition("@")[2] or "localhost"
    message_id_header = make_msgid(domain=domain)
    headers = {"Message-ID": message_id_header, **_thread_headers(conversation, message)}
    if message.is_ai:
        headers["Auto-Submitted"] = "auto-replied"
    email = EmailMessage(subject_for(conversation), text, formataddr((settings.SHOP_NAME, settings.SUPPORT_EMAIL)),
                         [conversation.email], headers=headers)
    try:
        email.send()
    except (smtplib.SMTPException, OSError):
        log.warning("Could not send support reply %s to %s", message.pk, conversation.email)
        raise
    message.email_message_id = message_id_header
    message.emailed_at = timezone.now()
    message.save(update_fields=["email_message_id", "emailed_at"])
    record("support.email_sent", obj=conversation, message=f"{message.get_sender_display()} reply")
