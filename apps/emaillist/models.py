"""The marketing email list: subscribers, their consent records, the
mailings the owner writes and approves, and the emails (deliveries) that
carry them.

A subscriber picks the most often they want to hear from us (weekly,
every two weeks, monthly).  Each approved mailing goes to every confirmed
subscriber; one who was mailed too recently gets it later, combined in
one email with whatever else was approved meanwhile (services.dispatch).
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


def new_token():
    return secrets.token_urlsafe(24)


class Subscriber(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for confirmation"
        SUBSCRIBED = "subscribed", "Subscribed"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"

    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "At most once a week"
        FORTNIGHTLY = "fortnightly", "At most once every two weeks"
        MONTHLY = "monthly", "At most once a month"

    # Days that must pass after one email before the next, for each choice.
    INTERVAL_DAYS = {Frequency.WEEKLY: 7, Frequency.FORTNIGHTLY: 14, Frequency.MONTHLY: 30}

    email = models.EmailField(max_length=254, unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    frequency = models.CharField(max_length=12, choices=Frequency.choices, default=Frequency.MONTHLY)
    # The secret in this subscriber's confirm, manage and unsubscribe links.
    # A new one is made each time they sign up again.
    token = models.CharField(max_length=64, unique=True, default=new_token, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    requested_at = models.DateTimeField(default=timezone.now, help_text="When they last asked to join")
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    # The local date of the last email we queued for them, for the cap.
    last_mailed_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def interval(self):
        return timedelta(days=self.INTERVAL_DAYS[self.frequency])

    def next_allowed_on(self):
        """The first local date we may email them again (None: any day)."""
        if self.last_mailed_on is None:
            return None
        return self.last_mailed_on + self.interval

    def is_due(self, today):
        allowed = self.next_allowed_on()
        return allowed is None or allowed <= today

    def confirm_expired(self, now=None):
        return (now or timezone.now()) > self.requested_at + settings.EMAIL_LIST_CONFIRM_WITHIN

    def manage_url(self):
        return reverse("emaillist:manage", args=[self.token])

    def unsubscribe_url(self):
        return reverse("emaillist:unsubscribe", args=[self.token])


class ConsentEvent(models.Model):
    """What a subscriber agreed to or withdrew, when, from where, and the
    exact words they were shown.  Never changed or deleted: the record that
    the list is opt-in."""

    class Action(models.TextChoices):
        REQUESTED = "requested", "Asked to join"
        CONFIRMED = "confirmed", "Confirmed by email"
        FREQUENCY = "frequency", "Changed how often"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"
        SUPPRESSED = "suppressed", "Removed by the shop"

    class Method(models.TextChoices):
        FORM = "form", "Form on the site"
        LINK = "link", "Link in an email"
        ONE_CLICK = "one-click", "One-click unsubscribe (mail app)"
        OWNER = "owner", "The owner"

    subscriber = models.ForeignKey(Subscriber, on_delete=models.PROTECT, related_name="consent_events")
    action = models.CharField(max_length=12, choices=Action.choices)
    method = models.CharField(max_length=12, choices=Method.choices)
    at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    # The email address and frequency at the time, and what the page said.
    email = models.EmailField(max_length=254)
    frequency = models.CharField(max_length=12, blank=True)
    wording = models.TextField(blank=True)

    class Meta:
        ordering = ["at", "pk"]

    def __str__(self):
        return f"{self.email}: {self.get_action_display()} {self.at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("Consent records cannot be changed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Consent records cannot be deleted.")


class Mailing(models.Model):
    """One piece of news for the list.  Nothing goes out until the owner
    approves it; then it goes to each subscriber as their frequency allows."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft, waiting for approval"
        APPROVED = "approved", "Approved"
        WITHDRAWN = "withdrawn", "Withdrawn"

    subject = models.CharField(
        max_length=120, help_text="The email's subject line.  Say plainly what is inside: the law (CAN-SPAM) forbids "
                                  "misleading subjects.")
    body = models.TextField(help_text="Plain text.  Leave a blank line between paragraphs.")
    send_until = models.DateField(
        null=True, blank=True, help_text="Optional, for news that goes stale (a sale that ends): the last day it may "
                                         "be sent.  Subscribers not due an email by then don't get it.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True, help_text="Who drafted it (the owner or an agent)")
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="+")
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject

    def is_current(self, today):
        return self.send_until is None or self.send_until >= today


class Delivery(models.Model):
    """One email to one subscriber, carrying one or more approved mailings."""

    subscriber = models.ForeignKey(Subscriber, on_delete=models.PROTECT, related_name="deliveries")
    mailings = models.ManyToManyField(Mailing, related_name="deliveries")
    subject = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    # Set instead of sent_at when the subscriber left before it went out.
    skipped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "deliveries"

    def __str__(self):
        return f"{self.subscriber}: {self.subject}"
