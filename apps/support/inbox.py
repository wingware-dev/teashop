"""The support inbox: customers' emails, read over IMAP by a job every few
minutes (SUPPORT_INBOX=imap), and passed to the assistant.

receive(raw) takes one email (bytes) and returns the customer Message it
became, or None when it is skipped:

- automatic mail (auto-replies, bounces, mailing lists, Auto-Submitted),
  and mail from the shop's own addresses, so robots can't talk to each
  other in a loop;
- an email seen before (the same Message-ID).

A reply threads into its conversation by In-Reply-To / References (our
replies' Message-IDs), else by the same sender and subject within 14 days.
Only the new text is kept, not the quoted history.
"""

import email
import imaplib
import logging
import re
from datetime import timedelta
from email import policy
from email.utils import parseaddr

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.html import strip_tags

from apps.audit import record

from . import services
from .models import Conversation, Message

log = logging.getLogger(__name__)

THREAD_WITHIN = timedelta(days=14)
AUTOMATIC_SENDERS = re.compile(r"^(mailer-daemon|postmaster|no-?reply|do-?not-?reply|bounces?)([+@.-]|$)",
                               re.IGNORECASE)
QUOTE_START = re.compile(r"^(On .{5,200}wrote:|-{2,} ?Original Message ?-{2,}|From: .+|Sent from my \w+)\s*$",
                         re.IGNORECASE | re.MULTILINE)


def is_automatic(message, sender):
    auto = (message.get("Auto-Submitted") or "no").strip().lower()
    if auto != "no":
        return "Auto-Submitted"
    if (message.get("Precedence") or "").strip().lower() in ("bulk", "junk", "list", "auto_reply"):
        return "Precedence"
    for header in ("List-Id", "List-Unsubscribe", "X-Autoreply", "X-Autorespond", "X-Auto-Response-Suppress"):
        if message.get(header):
            return header
    if AUTOMATIC_SENDERS.match(sender):
        return "sender"
    own = {parseaddr(addr)[1].lower() for addr in (settings.SUPPORT_EMAIL, settings.DEFAULT_FROM_EMAIL,
                                                   settings.EMAIL_LIST_FROM_EMAIL, settings.SERVER_EMAIL)}
    if sender in own:
        return "own address"
    return ""


def body_text(message):
    part = message.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    try:
        text = part.get_content()
    except (LookupError, UnicodeError):
        text = part.get_payload(decode=True).decode("utf-8", "replace")
    if part.get_content_type() == "text/html":
        text = strip_tags(re.sub(r"<(br|/p|/div)\b[^>]*>", "\n", text, flags=re.IGNORECASE))
    return text


def new_text(text):
    """text without the quoted earlier messages below it."""
    match = QUOTE_START.search(text)
    if match:
        text = text[:match.start()]
    lines = [line for line in text.splitlines() if not line.lstrip().startswith(">")]
    return "\n".join(lines).strip()


def _references(message):
    ids = " ".join(filter(None, [message.get("In-Reply-To", ""), message.get("References", "")]))
    return re.findall(r"<[^<>\s]+>", ids)


def _normal_subject(subject):
    return re.sub(r"^\s*((re|fwd?|aw)\s*:\s*)+", "", subject or "", flags=re.IGNORECASE).strip().lower()


def find_conversation(sender, subject, references):
    if references:
        known = Message.objects.filter(email_message_id__in=references).select_related("conversation").first()
        if known and known.conversation.email.lower() == sender:
            return known.conversation
    since = timezone.now() - THREAD_WITHIN
    wanted = _normal_subject(subject)
    for conversation in Conversation.objects.filter(channel=Conversation.Channel.EMAIL, email__iexact=sender,
                                                    last_activity_at__gte=since):
        if wanted and _normal_subject(conversation.subject) == wanted:
            return conversation
    return None


def receive(raw):
    message = email.message_from_bytes(raw, policy=policy.default)
    sender = parseaddr(str(message.get("From", "")))[1].strip().lower()
    message_id = str(message.get("Message-ID", "")).strip()[:250]
    subject = str(message.get("Subject", "")).strip()[:200]
    if not sender or "@" not in sender:
        log.info("Support inbox: skipped an email with no sender")
        return None
    automatic = is_automatic(message, sender)
    if automatic:
        log.info("Support inbox: skipped automatic email from %s (%s)", sender, automatic)
        return None
    if message_id and Message.objects.filter(email_message_id=message_id).exists():
        return None
    text = new_text(body_text(message)) or subject
    if not text:
        log.info("Support inbox: skipped an empty email from %s", sender)
        return None
    conversation = find_conversation(sender, subject, _references(message))
    if conversation is None:
        name = parseaddr(str(message.get("From", "")))[0][:100]
        conversation = Conversation.objects.create(channel=Conversation.Channel.EMAIL, email=sender, name=name,
                                                   subject=subject)
    try:
        return services.add_customer_message(conversation, text, email_message_id=message_id, subject=subject)
    except ValidationError as exc:
        log.warning("Support inbox: email from %s not kept: %s", sender, exc)
        return None


def poll():
    """Read the unread emails in the support mailbox, pass each to receive()
    and mark it read.  An email that can't be read is logged, recorded and
    marked read, so it doesn't stop the rest."""
    count = 0
    with imaplib.IMAP4_SSL(settings.SUPPORT_IMAP_HOST, settings.SUPPORT_IMAP_PORT, timeout=60) as imap:
        imap.login(settings.SUPPORT_IMAP_USER, settings.SUPPORT_IMAP_PASSWORD)
        imap.select(settings.SUPPORT_IMAP_FOLDER)
        status, data = imap.uid("search", None, "UNSEEN")
        if status != "OK":
            raise imaplib.IMAP4.error(f"IMAP search failed: {status}")
        for uid in data[0].split()[:50]:
            status, parts = imap.uid("fetch", uid, "(BODY.PEEK[])")
            raw = next((part[1] for part in parts if isinstance(part, tuple)), None) if status == "OK" else None
            if raw is None:
                continue
            try:
                with transaction.atomic():  # a savepoint: one bad email can't spoil the job's transaction
                    receive(raw)
                count += 1
            except Exception:
                log.exception("Support inbox: could not read email UID %s", uid)
                record("support.email_unreadable", message=f"IMAP UID {uid.decode()}; see the worker log")
            imap.uid("store", uid, "+FLAGS", "(\\Seen)")
    return count
