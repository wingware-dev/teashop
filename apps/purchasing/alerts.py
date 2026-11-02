"""Purchasing alerts for the owner dashboard: low items with no draft yet,
drafts waiting for approval, late deliveries, unfinished stock counts."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.core.attention import Attention
from apps.inventory.models import PurchaseOrder, PurchaseOrderLine

from . import services
from .models import StockCount


def attention_items():
    items = []
    drafted = set(PurchaseOrderLine.objects.filter(order__status=PurchaseOrder.Status.DRAFT).values_list("item_id", flat=True))
    suggested = services.suggestions()
    to_order = [r for r in suggested if not r.made_here and r.item.pk not in drafted]
    if to_order:
        items.append(
            Attention(
                title=f"Reorder: {len(to_order)} item{'s' if len(to_order) != 1 else ''} with no purchase order yet",
                detail=", ".join(r.item.name for r in to_order[:8]),
                url=reverse("purchasing:reorder"),
                kind="stock",
                key="purchasing:reorder",
            )
        )
    blends = [r for r in suggested if r.made_here]
    if blends:
        items.append(
            Attention(
                title=f"Make a blend batch: {', '.join(r.item.name for r in blends[:5])}",
                detail="Running low on blends made here",
                url=reverse("admin:inventory_blendbatch_add"),
                kind="stock",
                key="purchasing:blends",
            )
        )
    drafts = PurchaseOrder.objects.filter(status=PurchaseOrder.Status.DRAFT).select_related("supplier")
    for order in drafts[:10]:
        items.append(
            Attention(
                title=f"Purchase order for {order.supplier} waits for your approval",
                detail=f"{order.lines.count()} line(s); nothing is ordered until you approve it",
                url=reverse("admin:inventory_purchaseorder_change", args=[order.pk]),
                kind="purchase_orders",
                key=f"purchasing:draft:{order.pk}",
                since=order.created_at,
            )
        )
    today = timezone.localdate()
    late = PurchaseOrder.objects.filter(status__in=PurchaseOrder.OPEN, expected_on__lt=today).select_related("supplier")
    for order in late[:10]:
        items.append(
            Attention(
                title=f"Delivery late: {order} was expected {order.expected_on:%Y-%m-%d}",
                detail="Ask the supplier, or record the delivery if it came",
                url=reverse("admin:inventory_purchaseorder_change", args=[order.pk]),
                level="urgent",
                kind="purchase_orders",
                key=f"purchasing:late:{order.pk}",
            )
        )
    stale = timezone.now() - timedelta(days=7)
    for count in StockCount.objects.filter(status=StockCount.Status.OPEN, started_at__lt=stale)[:5]:
        items.append(
            Attention(
                title=f"{count} is not applied yet",
                detail="Finish counting and apply it, or delete it",
                url=reverse("admin:purchasing_stockcount_change", args=[count.pk]),
                kind="stock",
                key=f"purchasing:count:{count.pk}",
                since=count.started_at,
            )
        )
    return items
