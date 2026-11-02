"""The owner's side of page variants: the list waiting for approval, a
preview of each exactly as customers would see it, and approve, reject or
take down."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from apps.core.decorators import owner_required

from .models import PageVariant
from .views import product_context


@never_cache
@owner_required
def variant_list(request):
    variants = PageVariant.objects.select_related("product", "decided_by")
    return render(
        request,
        "storefront/owner/variant_list.html",
        {"waiting": variants.waiting(), "live": variants.live(),
         "decided": variants.exclude(status__in=[PageVariant.Status.DRAFT, PageVariant.Status.LIVE])[:30]},
    )


@never_cache
@owner_required
def variant_preview(request, pk):
    variant = get_object_or_404(PageVariant.objects.select_related("product__category", "product__tea"), pk=pk)
    context = product_context(request, variant.product, variant=variant)
    context["preview"] = variant
    context["problems"] = variant.copy_problems()
    return render(request, "storefront/product.html", context)


@require_POST
@owner_required
def variant_decide(request, pk):
    variant = get_object_or_404(PageVariant, pk=pk)
    decision = request.POST.get("decision")
    note = request.POST.get("note", "").strip()[:300]
    actions = {"approve": variant.approve, "reject": variant.reject, "take_down": variant.take_down}
    if decision not in actions:
        messages.error(request, "Choose approve, reject or take down.")
        return redirect(variant)
    try:
        actions[decision](request.user, note)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return redirect(variant)
    done = {"approve": "is now live", "reject": "was rejected", "take_down": "was taken down"}[decision]
    messages.success(request, f"The design for {variant.product} {done}.")
    return redirect("storefront:variant_list")
