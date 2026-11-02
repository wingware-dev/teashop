"""Fulfillment in the back office: the owner sets up scales, box sizes and
package dimensions here.  Parcels, packing records, labels, refunds and
delay notices are records, read-only here; they are made on the
fulfillment pages (/owner/fulfillment/)."""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (BoxSize, DelayNotice, PackageDimensions, PackedPackage, Parcel, ParcelLine, Pickup, PostageLabel,
                     Refund, Scale)


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def order_link(obj):
    order = obj.order if hasattr(obj, "order") else obj.parcel.order
    return format_html('<a href="{}">{}</a>', reverse("fulfillment:order", args=[order.number]), order.number)


order_link.short_description = "Order"


@admin.register(Scale)
class ScaleAdmin(admin.ModelAdmin):
    list_display = ["name", "serial_number", "ntep_certificate", "sealed_on", "inspection_due", "seal_intact",
                    "is_active"]
    list_filter = ["is_active", "seal_intact"]


@admin.register(BoxSize)
class BoxSizeAdmin(admin.ModelAdmin):
    list_display = ["item", "length_in", "width_in", "height_in", "empty_grams", "max_grams", "filler",
                    "filler_quantity", "stock", "is_active"]
    list_filter = ["is_active"]

    @admin.display(description="In stock")
    def stock(self, box):
        return box.item.on_hand()


@admin.register(PackageDimensions)
class PackageDimensionsAdmin(admin.ModelAdmin):
    list_display = ["size_option", "length_in", "width_in", "height_in"]
    search_fields = ["size_option__sku", "size_option__product__name"]


class ParcelLineInline(admin.TabularInline):
    model = ParcelLine
    extra = 0
    can_delete = False
    readonly_fields = ["order_line", "quantity"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Parcel)
class ParcelAdmin(ReadOnlyAdmin):
    list_display = ["__str__", order_link, "kind", "status", "created_at", "shipped_at"]
    list_filter = ["status", "kind"]
    search_fields = ["order__number", "order__email"]
    inlines = [ParcelLineInline]


@admin.register(PackedPackage)
class PackedPackageAdmin(ReadOnlyAdmin):
    """The packing record kept for weights and measures: what the scale
    showed for each package, and which scale (with its seal date)."""

    list_display = ["packed_at", order_link, "sold_package", "measured_grams", "scale_serial", "scale_sealed_on",
                    "allergens_confirmed", "label_printed_at", "reversed"]
    list_filter = ["scale"]
    search_fields = ["parcel__order__number", "sold_package__tea_lot__code", "scale_serial"]
    date_hierarchy = "packed_at"

    @admin.display(boolean=True, description="Unpacked")
    def reversed(self, package):
        return package.reversed


@admin.register(PostageLabel)
class PostageLabelAdmin(ReadOnlyAdmin):
    list_display = ["bought_at", order_link, "service", "tracking_number", "postage", "test_mode", "box_text",
                    "weight_grams", "pickup", "voided_at"]
    list_filter = ["test_mode", "service"]
    search_fields = ["tracking_number", "parcel__order__number"]
    date_hierarchy = "bought_at"


@admin.register(Pickup)
class PickupAdmin(ReadOnlyAdmin):
    list_display = ["pickup_date", "status", "confirmation", "location"]


@admin.register(Refund)
class RefundAdmin(ReadOnlyAdmin):
    list_display = ["created_at", order_link, "kind", "amount", "tax_amount", "reason", "provider_id", "email_sent_at"]
    list_filter = ["kind"]
    search_fields = ["order__number", "order__email", "provider_id"]
    date_hierarchy = "created_at"


@admin.register(DelayNotice)
class DelayNoticeAdmin(ReadOnlyAdmin):
    list_display = ["created_at", order_link, "old_ship_by", "new_ship_by", "needs_consent", "answer_by", "response",
                    "sent_at"]
    list_filter = ["response", "needs_consent"]
