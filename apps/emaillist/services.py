"""The email list's rules: signing up with a confirmation email, consent
records, unsubscribing, approving mailings, and sending each subscriber
what is waiting for them no more often than they chose.

Every change to a subscriber's consent goes through here, so each one
leaves a ConsentEvent.  The sending itself is in sending.py.
"""

import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps import jobs
from apps.audit import agent_involved, current_actor, record

from .models import ConsentEvent, Delivery, Mailing, Subscriber, new_token

log = logging.getLogger(__name__)

# What the sign-up form says, kept with each sign-up as the words agreed to.
SIGN_UP_WORDING = (
    "Email me news from {shop}: new teas, restocks, tea notes and offers, no more often than I choose below.  "
    "I'll get an email to confirm first.  Every email has a link to unsubscribe or change how often."
)


def sign_up_wording():
    return SIGN_UP_WORDING.format(shop=settings.SHOP_NAME)


def normalize(email):
    return email.strip().lower()


def _event(subscriber, action, method, *, ip=None, user_agent="", wording=""):
    return ConsentEvent.objects.create(
        subscriber=subscriber, action=action, method=method, ip_address=ip or None,
        user_agent=(user_agent or "")[:300], email=subscriber.email, frequency=subscriber.frequency, wording=wording)


# -- Subscribers ---------------------------------------------------------------

def request_sign_up(email, frequency, *, ip=None, user_agent="", wording=None):
    """Someone asked to join from the form.  New, pending or unsubscribed:
    they wait for confirmation and we email them a link.  Already
    subscribed: we email them their settings link instead, so the form
    can't be used to change someone else's settings or to learn who is on
    the list.  Returns the Subscriber."""
    email = normalize(email)
    if frequency not in Subscriber.Frequency.values:
        raise ValidationError(f"Unknown frequency {frequency!r}")
    from . import sending

    with transaction.atomic():
        subscriber, _ = Subscriber.objects.select_for_update().get_or_create(email=email)
        if subscriber.status == Subscriber.Status.SUBSCRIBED:
            jobs.enqueue(sending.send_already_subscribed, subscriber.pk, key=f"emaillist-already:{subscriber.pk}")
            return subscriber
        subscriber.status = Subscriber.Status.PENDING
        subscriber.frequency = frequency
        subscriber.token = new_token()
        subscriber.requested_at = timezone.now()
        subscriber.confirmation_sent_at = None
        subscriber.save()
        _event(subscriber, ConsentEvent.Action.REQUESTED, ConsentEvent.Method.FORM, ip=ip, user_agent=user_agent,
               wording=wording if wording is not None else sign_up_wording())
        jobs.enqueue(sending.send_confirmation, subscriber.pk, key=f"emaillist-confirm:{subscriber.pk}")
    return subscriber


def by_token(token):
    return Subscriber.objects.filter(token=token).first() if token else None


def confirm(subscriber, *, ip=None, user_agent=""):
    """The subscriber followed the link in the confirmation email.  Returns
    "confirmed", "already" (nothing to do) or "expired"."""
    with transaction.atomic():
        subscriber = Subscriber.objects.select_for_update().get(pk=subscriber.pk)
        if subscriber.status == Subscriber.Status.SUBSCRIBED:
            return "already"
        if subscriber.status != Subscriber.Status.PENDING or subscriber.confirm_expired():
            return "expired"
        subscriber.status = Subscriber.Status.SUBSCRIBED
        subscriber.confirmed_at = timezone.now()
        subscriber.unsubscribed_at = None
        subscriber.save()
        _event(subscriber, ConsentEvent.Action.CONFIRMED, ConsentEvent.Method.LINK, ip=ip, user_agent=user_agent)
    return "confirmed"


def set_frequency(subscriber, frequency, *, ip=None, user_agent=""):
    if frequency not in Subscriber.Frequency.values:
        raise ValidationError(f"Unknown frequency {frequency!r}")
    with transaction.atomic():
        subscriber = Subscriber.objects.select_for_update().get(pk=subscriber.pk)
        if subscriber.frequency == frequency:
            return subscriber
        subscriber.frequency = frequency
        subscriber.save(update_fields=["frequency"])
        _event(subscriber, ConsentEvent.Action.FREQUENCY, ConsentEvent.Method.LINK, ip=ip, user_agent=user_agent)
    return subscriber


def unsubscribe(subscriber, method=ConsentEvent.Method.LINK, *, ip=None, user_agent="", user=None):
    """Take them off the list at once (CAN-SPAM allows 10 business days; we
    don't wait).  Emails already queued for them are skipped.  Returns
    False if they were already off it."""
    action = ConsentEvent.Action.SUPPRESSED if method == ConsentEvent.Method.OWNER else ConsentEvent.Action.UNSUBSCRIBED
    with transaction.atomic():
        subscriber = Subscriber.objects.select_for_update().get(pk=subscriber.pk)
        if subscriber.status == Subscriber.Status.UNSUBSCRIBED:
            return False
        subscriber.status = Subscriber.Status.UNSUBSCRIBED
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save()
        _event(subscriber, action, method, ip=ip, user_agent=user_agent,
               wording=f"By {user}" if user is not None else "")
    return True


# -- Mailings ------------------------------------------------------------------

def draft_mailing(subject, body, send_until=None, created_by=""):
    """A new draft: what the owner's form and a marketing agent use.  It
    waits for the owner's approval."""
    return Mailing.objects.create(subject=subject.strip(), body=body.strip(), send_until=send_until,
                                  created_by=created_by or current_actor().label)


def approval_problems(mailing, today=None):
    """Reasons the mailing can't be approved now, as sentences."""
    today = today or timezone.localdate()
    problems = []
    if mailing.status != Mailing.Status.DRAFT:
        problems.append(f"It is {mailing.get_status_display().lower()}, not a draft.")
    if not settings.SHOP_POSTAL_ADDRESS.strip():
        problems.append("The shop's postal address is not set (SHOP_POSTAL_ADDRESS).  The law (CAN-SPAM) requires it "
                        "in every marketing email; a registered PO box will do.")
    if not mailing.subject.strip() or not mailing.body.strip():
        problems.append("It needs a subject and some text.")
    if mailing.send_until and mailing.send_until < today:
        problems.append(f"Its last day to send ({mailing.send_until:%B %-d}) has passed.")
    return problems


def approve(mailing, user):
    """The owner approves a draft: from now on it goes to every confirmed
    subscriber as their frequency allows, starting with those due today.
    Nothing else releases a mailing; AI agents can draft but never
    approve."""
    if agent_involved():
        raise PermissionDenied("AI agents cannot approve mailings.")
    if user is None or not user.is_authenticated or not user.is_staff:
        raise PermissionDenied("Only the owner can approve mailings.")
    with transaction.atomic():
        mailing = Mailing.objects.select_for_update().get(pk=mailing.pk)
        problems = approval_problems(mailing)
        if problems:
            raise ValidationError(problems)
        mailing.status = Mailing.Status.APPROVED
        mailing.approved_at = timezone.now()
        mailing.approved_by = user
        mailing.save()
        record("emaillist.mailing_approved", obj=mailing, message=mailing.subject)
        from . import jobs as list_jobs

        jobs.enqueue(list_jobs.dispatch_due, key="emaillist:dispatch")
    return mailing


def withdraw(mailing):
    """Stop a mailing: a draft is dropped, an approved one goes to nobody
    else (emails already sent stay sent)."""
    with transaction.atomic():
        mailing = Mailing.objects.select_for_update().get(pk=mailing.pk)
        if mailing.status == Mailing.Status.WITHDRAWN:
            return mailing
        mailing.status = Mailing.Status.WITHDRAWN
        mailing.withdrawn_at = timezone.now()
        mailing.save()
    return mailing


# -- Combining and sending -----------------------------------------------------

def current_mailings(today):
    """Approved mailings that may still be sent, oldest approval first."""
    return list(Mailing.objects.filter(status=Mailing.Status.APPROVED, approved_at__isnull=False)
                .exclude(send_until__lt=today).order_by("approved_at", "pk"))


def waiting_for(subscriber, mailings, received):
    """Of mailings, those this subscriber should get and hasn't: approved
    after they confirmed (no back issues), and in none of their emails.
    received: the mailing ids already in their emails."""
    if subscriber.confirmed_at is None:
        return []
    return [m for m in mailings if m.approved_at >= subscriber.confirmed_at and m.pk not in received]


def combined_subject(mailings):
    """An honest subject for one email carrying these mailings (newest
    first): the newest one's subject, and how many more are inside."""
    newest = mailings[0].subject
    more = len(mailings) - 1
    return newest if not more else f"{newest}, and {more} more update{'s' if more > 1 else ''}"


def _received(subscriber_ids, mailings):
    received = {}
    rows = Delivery.mailings.through.objects.filter(
        delivery__subscriber_id__in=subscriber_ids, mailing__in=mailings).values_list("delivery__subscriber_id",
                                                                                      "mailing_id")
    for subscriber_id, mailing_id in rows:
        received.setdefault(subscriber_id, set()).add(mailing_id)
    return received


def dispatch(today=None):
    """Queue an email for each confirmed subscriber who is due one (their
    frequency allows it today) and has approved mailings waiting, carrying
    all of them in one email.  The others wait for a later day.  One job per
    email, each with its own retries.  Returns the number queued."""
    from . import sending

    today = today or timezone.localdate()
    if not settings.SHOP_POSTAL_ADDRESS.strip():
        log.warning("Email list: no SHOP_POSTAL_ADDRESS, so no mailings are sent (CAN-SPAM requires one)")
        return 0
    mailings = current_mailings(today)
    if not mailings:
        return 0
    subscribers = [s for s in Subscriber.objects.filter(status=Subscriber.Status.SUBSCRIBED) if s.is_due(today)]
    received = _received([s.pk for s in subscribers], mailings)
    queued = 0
    for subscriber in subscribers:
        if not waiting_for(subscriber, mailings, received.get(subscriber.pk, set())):
            continue
        with transaction.atomic():
            # Check again under the lock: a frequency change or another
            # dispatch may have come in between.
            subscriber = Subscriber.objects.select_for_update().get(pk=subscriber.pk)
            if subscriber.status != Subscriber.Status.SUBSCRIBED or not subscriber.is_due(today):
                continue
            already = set(Delivery.mailings.through.objects.filter(delivery__subscriber=subscriber)
                          .values_list("mailing_id", flat=True))
            carried = list(reversed(waiting_for(subscriber, mailings, already)))
            if not carried:
                continue
            delivery = Delivery.objects.create(subscriber=subscriber, subject=combined_subject(carried)[:200])
            delivery.mailings.set(carried)
            subscriber.last_mailed_on = today
            subscriber.save(update_fields=["last_mailed_on"])
            jobs.enqueue(sending.send_delivery, delivery.pk, key=f"emaillist-delivery:{delivery.pk}")
            queued += 1
    if queued:
        log.info("Email list: queued %d email(s)", queued)
    return queued


def reach(mailing, today=None):
    """(sent, waiting): emails sent carrying this mailing, and confirmed
    subscribers who will still get it."""
    today = today or timezone.localdate()
    sent = mailing.deliveries.exclude(sent_at=None).count()
    if mailing.status != Mailing.Status.APPROVED or not mailing.is_current(today):
        return sent, 0
    have = set(mailing.deliveries.values_list("subscriber_id", flat=True))
    waiting = Subscriber.objects.filter(status=Subscriber.Status.SUBSCRIBED, confirmed_at__lte=mailing.approved_at) \
        .exclude(pk__in=have).count()
    return sent, waiting
