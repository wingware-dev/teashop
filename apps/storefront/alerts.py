"""Storefront items for the owner dashboard: page designs waiting for
approval, and shown products whose copy breaks the rules (they can get
in without the admin's checks, for example from an import)."""

from django.urls import reverse

from apps.core.attention import Attention

from .browsing import shown_products
from .models import PageVariant


def attention_items():
    items = []
    waiting = PageVariant.objects.waiting().count()
    if waiting:
        items.append(
            Attention(
                title=f"Page designs waiting for your approval: {waiting}",
                detail="AI-made designs for tea pages; none goes live until you approve it.",
                url=reverse("storefront:variant_list"),
                level="warning",
                kind="approvals",
                key="storefront:designs-waiting",
                since=PageVariant.objects.waiting().order_by("created_at").values_list("created_at", flat=True).first(),
            )
        )
    bad = [product for product in shown_products() if product.copy_problems()]
    if bad:
        items.append(
            Attention(
                title=f"Product wording to fix: {len(bad)}",
                detail=", ".join(p.name for p in bad[:8]) + (" ..." if len(bad) > 8 else "")
                + ".  Health claims, herbal names or protected origins; open each product to see what.",
                url=reverse("admin:catalog_product_changelist"),
                level="urgent",
                kind="problems",
                key="storefront:wording",
            )
        )
    return items
