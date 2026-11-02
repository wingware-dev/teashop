"""Catalog alerts for the owner dashboard: organic sales nearing the limit
for selling organic without certification, and sizes that cannot be
packed from current stock."""

from django.conf import settings
from django.urls import reverse

from apps.core.attention import Attention

from . import services
from .models import SizeOption


def organic_alert():
    total = services.organic_sales()
    limit = settings.ORGANIC_EXEMPTION_LIMIT
    if total < settings.ORGANIC_SALES_ALERT:
        return None
    over = total >= limit
    return Attention(
        title=f"Organic sales this year: ${total:,.2f} of the ${limit:,.0f} limit",
        detail=(
            "Over the limit: stop selling as organic, or get organic handler certification."
            if over
            else "Plan now: get organic handler certification, or stop selling as organic before the limit."
        ),
        url=reverse("admin:catalog_soldpackage_changelist") + "?organic__exact=1",
        level="urgent" if over else "warning",
        kind="other",
        key=f"catalog:organic:{'over' if over else 'near'}",
    )


def unpackable_sizes():
    sizes = SizeOption.objects.filter(is_active=True, product__is_active=True).select_related("product__tea")
    return [size for size in sizes if size.packages_available() == 0]


def attention_items():
    items = []
    alert = organic_alert()
    if alert:
        items.append(alert)
    sizes = unpackable_sizes()
    if sizes:
        names = ", ".join(str(size) for size in sizes[:8]) + (f" and {len(sizes) - 8} more" if len(sizes) > 8 else "")
        items.append(
            Attention(
                title=f"Can't be packed from stock: {len(sizes)} size{'s' if len(sizes) != 1 else ''}",
                detail=names,
                url=reverse("admin:catalog_sizeoption_changelist"),
                level="urgent",
                kind="stock",
                key="catalog:unpackable",
            )
        )
    return items
