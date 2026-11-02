"""Fulfillment items for the owner dashboard's "Needs your attention" list.
(Orders near or past their promised ship date are checkout's items; they
link to the queue here.)"""

from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.checkout.models import Order
from apps.core.attention import Attention

from .models import BoxSize, DelayNotice, PackedPackage, Parcel, PostageLabel, Scale
from .services import consent_overdue


def attention_items():
    items = []
    today = timezone.localdate()
    queue = reverse("fulfillment:queue")
    for notice in consent_overdue(today):
        items.append(Attention(
            f"Order {notice.order.number}: no answer to the delay notice",
            "The customer did not agree to the longer delay.  The Mail Order Rule says cancel the order and refund "
            "it in full now.", reverse("fulfillment:order", args=[notice.order.number]), "urgent"))
    waiting = DelayNotice.objects.filter(needs_consent=True, response=DelayNotice.Response.WAITING,
                                         order__status=Order.Status.PAID, answer_by__gte=today).count()
    if waiting:
        items.append(Attention(f"Delay notices waiting for the customer's answer: {waiting}",
                               "Ship as soon as you can; if no answer comes by the date given, cancel and refund.",
                               queue, "warning"))
    # Queued notices go out within seconds; one unsent after 10 minutes is
    # failing (the job queue keeps retrying it).
    unsent = DelayNotice.objects.filter(sent_at=None, order__status=Order.Status.PAID,
                                        created_at__lt=timezone.now() - timedelta(minutes=10)).count()
    if unsent:
        items.append(Attention(f"Delay notices not sent yet: {unsent}",
                               "The email is failing and is tried again automatically.  Check the email settings; "
                               "if its job has failed for good, use \"Run again\" on it (Background jobs).",
                               queue, "urgent"))
    late_backorders = Parcel.objects.filter(status=Parcel.Status.BACKORDERED, expected_on__lt=today).count()
    if late_backorders:
        items.append(Attention(f"Back-orders past their expected date: {late_backorders}",
                               "Check the stock; the customer may need a delay notice.", queue, "warning"))

    paid = Order.objects.filter(status=Order.Status.PAID)
    scales = list(Scale.objects.filter(is_active=True))
    if paid.exists() and not any(scale.usable for scale in scales):
        items.append(Attention("No sealed scale is set up for packing",
                               "Add your legal-for-trade scale with its serial number and seal date "
                               "(Fulfillment → Scales).", reverse("admin:fulfillment_scale_changelist"), "urgent"))
    for scale in scales:
        if not scale.seal_intact:
            items.append(Attention(f"{scale}: the seal is broken",
                                   "Have weights and measures inspect and seal it before packing on it again.",
                                   reverse("admin:fulfillment_scale_change", args=[scale.pk]), "urgent"))
        elif scale.inspection_overdue(today):
            items.append(Attention(f"{scale}: inspection due since {scale.inspection_due:%B %-d}",
                                   "Ask your county weights and measures office to inspect it.",
                                   reverse("admin:fulfillment_scale_change", args=[scale.pk]), "warning"))
    if paid.exists() and not BoxSize.objects.filter(is_active=True).exists():
        items.append(Attention("No box sizes are set up",
                               "Add your boxes and mailers with their inside sizes (Fulfillment → Box sizes) for "
                               "box suggestions and box stock.", reverse("admin:fulfillment_boxsize_changelist")))
    for box in BoxSize.objects.filter(is_active=True).select_related("item"):
        if box.item.is_low():
            items.append(Attention(f"Running low on {box.item}: {box.item.on_hand()} left", "",
                                   reverse("purchasing:reorder"), "warning"))
    unprinted = PackedPackage.objects.filter(sold_package__reversed_at=None, label_printed_at=None,
                                             sold_package__tea_lot__isnull=False,
                                             parcel__status__in=Parcel.ACTIVE_STATUSES).count()
    if unprinted:
        items.append(Attention(f"Packed packages without a printed label: {unprinted}",
                               "Each pouch or tin needs its label before it ships.", queue, "warning"))
    if settings.PRODUCTION and PostageLabel.objects.filter(test_mode=True, voided_at=None,
                                                           parcel__status=Parcel.Status.SHIPPED,
                                                           bought_at__date=today).exists():
        items.append(Attention("Today's shipping labels are test labels",
                               "EasyPost is in test mode: these labels carry no postage and must not be mailed.",
                               queue, "urgent"))
    return items
