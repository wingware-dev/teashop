import secrets

from django.db import models
from django.urls import reverse
from django.utils import timezone


def new_token():
    return secrets.token_urlsafe(24)


class Category(models.TextChoices):
    """What a question is about.  The first three are the clear-cut kinds
    the agent may answer; anything else goes to the owner."""

    ORDER_STATUS = "order_status", "Order status and tracking"
    BREWING = "brewing", "Brewing advice"
    SHIPPING = "shipping", "Shipping times and costs"
    OTHER = "other", "Other (always to you)"


ANSWERABLE = (Category.ORDER_STATUS, Category.BREWING, Category.SHIPPING)


class Conversation(models.Model):
    class Channel(models.TextChoices):
        CHAT = "chat", "Chat"
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        OPEN = "open", "With the assistant"
        DRAFTED = "drafted", "Draft for you to check"
        ESCALATED = "escalated", "Waiting for you"
        ANSWERED = "answered", "Answered"
        CLOSED = "closed", "Closed"

    WAITING = (Status.DRAFTED, Status.ESCALATED)

    channel = models.CharField(max_length=5, choices=Channel.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True)
    category = models.CharField(max_length=12, choices=Category.choices, blank=True)
    email = models.EmailField(help_text="As the customer gave it (chat) or the sender (email); not verified")
    name = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    # The secret in the customer's chat link.
    token = models.CharField(max_length=40, unique=True, default=new_token, editable=False)
    order = models.ForeignKey("checkout.Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                              help_text="The order the assistant found for it")
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalation_reason = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    last_activity_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-last_activity_at", "-pk"]

    def __str__(self):
        return f"{self.get_channel_display()} with {self.email}" + (f": {self.subject}" if self.subject else "")

    def get_absolute_url(self):
        return reverse("support:owner_conversation", args=[self.pk])

    def chat_url(self):
        return reverse("support:chat", args=[self.token])

    def pending_draft(self):
        return self.drafts.filter(status=Draft.Status.PENDING).order_by("-pk").first()


class Message(models.Model):
    class Sender(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        AGENT = "agent", "AI assistant"
        OWNER = "owner", "The shop"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=8, choices=Sender.choices)
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    # Outgoing email: when it went; incoming or outgoing: its Message-ID,
    # for threading replies.
    email_message_id = models.CharField(max_length=250, blank=True, db_index=True)
    emailed_at = models.DateTimeField(null=True, blank=True)
    # Customer messages: when the assistant dealt with it.
    handled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"{self.get_sender_display()} at {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def is_ai(self):
        return self.sender == self.Sender.AGENT


class Draft(models.Model):
    """In watch mode: the assistant's reply, for the owner to edit and send.
    What the owner sent is kept beside it; those pairs teach the assistant
    the owner's voice, and how often drafts go out unchanged says when a
    category is ready to answer on its own."""

    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for you"
        SENT = "sent", "Sent"
        DISCARDED = "discarded", "Discarded"
        # The customer wrote again, or the owner replied without it: it
        # doesn't count either way.
        REPLACED = "replaced", "Replaced"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="drafts")
    category = models.CharField(max_length=12, choices=Category.choices)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    sent_body = models.TextField(blank=True)
    # How close what was sent is to the draft (1.0: unchanged).
    similarity = models.FloatField(null=True, blank=True)
    approved = models.BooleanField(null=True, help_text="Sent with no or small edits")
    created_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"Draft for {self.conversation}"


class CategoryMode(models.Model):
    """Whether the assistant answers a category on its own (the owner turns
    it on once the approval rate says it is ready) or drafts for the owner
    (watch mode, the default)."""

    category = models.CharField(max_length=12, choices=Category.choices, unique=True)
    answers_alone = models.BooleanField(default=False)
    changed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_category_display()}: {'answers alone' if self.answers_alone else 'watch mode'}"
