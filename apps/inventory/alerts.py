"""Stock alerts for the owner dashboard: low stock, lots near their
best-by date, lots on hold."""

from datetime import timedelta

from django.conf import settings
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone

from apps.core.attention import Attention

from .models import Item, Lot


def low_stock_items():
    """Active items with a reorder level whose usable stock is at or below it,
    as [(item, on_hand)]."""
    usable = Q(lots__status=Lot.Status.ACTIVE, lots__quantity_on_hand__gt=0)
    items = (
        Item.objects.filter(is_active=True, reorder_level__gt=0)
        .annotate(usable_on_hand=Sum("lots__quantity_on_hand", filter=usable, default=0))
        .order_by("name")
    )
    return [(item, item.usable_on_hand) for item in items if item.usable_on_hand <= item.reorder_level]


def lots_near_best_by(days=None):
    days = settings.INVENTORY_BEST_BY_WARNING_DAYS if days is None else days
    cutoff = timezone.localdate() + timedelta(days=days)
    return Lot.objects.usable().filter(best_by__lte=cutoff).select_related("item").order_by("best_by")


def attention_items():
    admin = reverse("admin:index")
    items = []
    low = low_stock_items()
    if low:
        names = ", ".join(
            f"{item.name} ({item.format_quantity(on_hand)})" for item, on_hand in low[:8]
        ) + (f" and {len(low) - 8} more" if len(low) > 8 else "")
        items.append(
            Attention(
                title=f"Low stock: {len(low)} item{'s' if len(low) != 1 else ''}",
                detail=names,
                url=admin + "inventory/item/?stock=low",
                level="urgent" if any(on_hand == 0 for _, on_hand in low) else "warning",
            )
        )
    today = timezone.localdate()
    for lot in lots_near_best_by()[:10]:
        past = lot.best_by < today
        items.append(
            Attention(
                title=f"Lot {lot.code} {'is past' if past else 'nears'} its best-by date ({lot.best_by:%Y-%m-%d})",
                detail=f"{lot.item}: {lot.format_quantity(lot.quantity_on_hand)} left",
                url=reverse("admin:inventory_lot_change", args=[lot.pk]),
                level="urgent" if past else "warning",
            )
        )
    held = Lot.objects.filter(status=Lot.Status.ON_HOLD, quantity_on_hand__gt=0).select_related("item")
    for lot in held[:10]:
        items.append(
            Attention(
                title=f"Lot {lot.code} is on hold",
                detail=lot.status_note or f"{lot.item}: {lot.format_quantity(lot.quantity_on_hand)}",
                url=reverse("admin:inventory_lot_change", args=[lot.pk]),
            )
        )
    return items
