"""Sending the email list's emails, each as its own job (apps.jobs) so each
retries on its own.

- The confirmation and "already subscribed" emails go the way of the
  shop's other emails (checkout.emails.send_now, the main mail server).
- Mailings go through the bulk sender when EMAIL_LIST_EMAIL_HOST is set
  (Amazon SES's SMTP interface; docs/emaillist.md), else the main mail
  server.  Each carries List-Unsubscribe and List-Unsubscribe-Post headers
  (RFC 8058), which Gmail and Yahoo require of bulk senders and which
  their "Unsubscribe" button uses, and an unsubscribe link and the shop's
  postal address in the text (CAN-SPAM).
"""

import logging
import smtplib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps import jobs
from apps.audit import record
from apps.checkout.emails import EMAIL_ATTEMPTS, absolute, send_now

from .models import Delivery, Mailing, Subscriber

log = logging.getLogger(__name__)


def connection():
    """The mail connection for mailings: the bulk sender if one is set."""
    if settings.EMAIL_LIST_EMAIL_HOST:
        return get_connection(
            "django.core.mail.backends.smtp.EmailBackend", host=settings.EMAIL_LIST_EMAIL_HOST,
            port=settings.EMAIL_LIST_EMAIL_PORT, username=settings.EMAIL_LIST_EMAIL_HOST_USER,
            password=settings.EMAIL_LIST_EMAIL_HOST_PASSWORD, use_tls=True, timeout=20)
    return get_connection()


def _subscriber(subscriber_id):
    subscriber = Subscriber.objects.filter(pk=subscriber_id).first()
    if subscriber is None:
        log.warning("Subscriber %s no longer exists; its email is not sent", subscriber_id)
    return subscriber


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_confirmation(subscriber_id):
    subscriber = _subscriber(subscriber_id)
    if subscriber is None or subscriber.status != Subscriber.Status.PENDING or subscriber.confirmation_sent_at:
        return
    send_now(f"Please confirm: {settings.SHOP_NAME}'s email list", "confirm", {
        "subscriber": subscriber, "confirm_url": absolute(reverse("emaillist:confirm", args=[subscriber.token])),
        "confirm_days": settings.EMAIL_LIST_CONFIRM_WITHIN.days,
    }, subscriber.email, subscriber, app="emaillist")
    subscriber.confirmation_sent_at = timezone.now()
    subscriber.save(update_fields=["confirmation_sent_at"])


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_already_subscribed(subscriber_id):
    subscriber = _subscriber(subscriber_id)
    if subscriber is None or subscriber.status != Subscriber.Status.SUBSCRIBED:
        return
    send_now(f"You're already on {settings.SHOP_NAME}'s email list", "already_subscribed", {
        "subscriber": subscriber, "manage_url": absolute(subscriber.manage_url()),
    }, subscriber.email, subscriber, app="emaillist")


def render_mailing(subscriber, mailings):
    """The text of one email carrying these mailings to this subscriber."""
    return render_to_string("emaillist/email/mailing.txt", {
        "shop_name": settings.SHOP_NAME,
        "postal_address": settings.SHOP_POSTAL_ADDRESS,
        "site_url": settings.SITE_URL.rstrip("/"),
        "subscriber": subscriber,
        "mailings": mailings,
        "manage_url": absolute(subscriber.manage_url()),
        "unsubscribe_url": absolute(subscriber.unsubscribe_url()),
    })


def build_message(subscriber, subject, mailings, conn=None):
    unsubscribe = absolute(subscriber.unsubscribe_url())
    return EmailMessage(
        subject, render_mailing(subscriber, mailings), settings.EMAIL_LIST_FROM_EMAIL, [subscriber.email],
        reply_to=[settings.SHOP_CONTACT_EMAIL], connection=conn,
        headers={
            "List-Unsubscribe": f"<{unsubscribe}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            "List-Id": f"{settings.SHOP_NAME} news <{settings.EMAIL_LIST_ID}>",
            "Precedence": "bulk",
        })


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_delivery(delivery_id):
    """Send one queued email.  Skipped, not sent, if the subscriber left or
    every mailing in it was withdrawn since it was queued."""
    delivery = Delivery.objects.select_related("subscriber").filter(pk=delivery_id).first()
    if delivery is None or delivery.sent_at or delivery.skipped_at:
        return
    subscriber = delivery.subscriber
    mailings = list(delivery.mailings.filter(status=Mailing.Status.APPROVED).order_by("-approved_at", "-pk"))
    if subscriber.status != Subscriber.Status.SUBSCRIBED or not mailings:
        delivery.skipped_at = timezone.now()
        delivery.save(update_fields=["skipped_at"])
        return
    if not settings.SHOP_POSTAL_ADDRESS.strip():
        raise ImproperlyConfigured("SHOP_POSTAL_ADDRESS is not set; marketing email must carry it (CAN-SPAM)")
    try:
        build_message(subscriber, delivery.subject, mailings, connection()).send()
    except (smtplib.SMTPException, OSError):
        log.warning("Could not send %r to %s", delivery.subject, subscriber.email)
        raise
    record("emaillist.email_sent", obj=delivery, message=delivery.subject)
    delivery.sent_at = timezone.now()
    delivery.save(update_fields=["sent_at"])
