"""Email list items for the owner dashboard's "Needs your attention" queue:
mailings waiting for approval, and sending that is stuck."""

from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.core.attention import Attention

from .models import Delivery, Mailing, Subscriber


def attention_items():
    items = []
    home = reverse("emaillist:owner_home")
    for mailing in Mailing.objects.filter(status=Mailing.Status.DRAFT).order_by("created_at"):
        items.append(Attention(
            f"Mailing to approve: {mailing.subject}",
            f"Drafted by {mailing.created_by}.  Nothing goes to the list until you approve it."
            if mailing.created_by else "Nothing goes to the list until you approve it.",
            reverse("emaillist:mailing", args=[mailing.pk]), "warning",
            kind="approvals", key=f"emaillist:mailing:{mailing.pk}", since=mailing.created_at))
    has_list = Subscriber.objects.filter(status=Subscriber.Status.SUBSCRIBED).exists()
    if not settings.SHOP_POSTAL_ADDRESS.strip() and (has_list or Mailing.objects.filter(
            status__in=[Mailing.Status.DRAFT, Mailing.Status.APPROVED]).exists()):
        items.append(Attention(
            "Mailings can't go out: no postal address",
            "The law (CAN-SPAM) requires the shop's postal address in every marketing email; a registered PO box "
            "will do.  Set SHOP_POSTAL_ADDRESS in .env and redeploy.", home, "urgent",
            kind="problems", key="emaillist:no-postal-address"))
    # Queued emails go out within minutes; one unsent after 30 is failing
    # (the job queue keeps retrying it).
    stuck = Delivery.objects.filter(sent_at=None, skipped_at=None,
                                    created_at__lt=timezone.now() - timedelta(minutes=30))
    if stuck.exists():
        items.append(Attention(
            f"Mailing emails not sent yet: {stuck.count()}",
            "Sending is failing and is tried again automatically.  Check the email list's mail settings "
            "(EMAIL_LIST_EMAIL_HOST); if a job has failed for good, use \"Run again\" on it (Background jobs).",
            home, "urgent", kind="problems", key="emaillist:stuck",
            since=stuck.order_by("created_at").first().created_at))
    return items
