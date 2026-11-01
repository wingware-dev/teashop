from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from . import services
from .models import BomLine, Product, SizeOption, SoldPackage


class SizeOptionInline(admin.TabularInline):
    model = SizeOption
    extra = 1
    fields = ["name", "sku", "net_grams", "price", "sort_order", "is_active", "available"]
    readonly_fields = ["available"]
    show_change_link = True

    @admin.display(description="Packable now")
    def available(self, size):
        return size.packages_available() if size.pk else "—"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "tea", "sold_as_organic", "is_active"]
    list_filter = ["kind", "sold_as_organic", "is_active"]
    search_fields = ["name", "label_name", "tea__name"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = ["tea"]
    inlines = [SizeOptionInline]


class BomLineInline(admin.TabularInline):
    model = BomLine
    extra = 2
    autocomplete_fields = ["item"]
    verbose_name_plural = "Bill of materials besides the tea (tin or pouch, label, ...)"


@admin.register(SizeOption)
class SizeOptionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "sku", "net_grams", "price", "available", "is_active"]
    list_filter = ["is_active", "product__kind"]
    search_fields = ["name", "sku", "product__name"]
    autocomplete_fields = ["product"]
    list_select_related = ["product__tea"]
    readonly_fields = ["bill_of_materials_display", "net_weight_label", "available"]
    fields = ["product", "name", "sku", "net_grams", "price", "sort_order", "is_active"] + readonly_fields
    inlines = [BomLineInline]

    @admin.display(description="Packable now")
    def available(self, size):
        return size.packages_available() if size.pk else "—"

    @admin.display(description="One package uses")
    def bill_of_materials_display(self, size):
        if not size.pk:
            return "—"
        lines = size.bill_of_materials()
        if not lines:
            return "Nothing yet"
        return format_html_join(format_html("<br>"), "{}", ((f"{item.format_quantity(qty)} {item}",) for item, qty in lines))

    @admin.display(description="Net weight on the label")
    def net_weight_label(self, size):
        return services.net_weight_text(size.net_grams) if size.net_grams else "—"


@admin.register(SoldPackage)
class SoldPackageAdmin(admin.ModelAdmin):
    """Packages packed for orders, read-only: the link from a customer
    order to a tea lot, and the organic sales total."""

    list_display = ["packed_at", "order_reference", "size_option", "lot_link", "tea_grams", "amount", "organic"]
    list_filter = ["organic", "size_option__product"]
    search_fields = ["order_reference", "tea_lot__code", "size_option__sku", "size_option__product__name"]
    date_hierarchy = "packed_at"
    list_select_related = ["size_option__product", "tea_lot"]
    readonly_fields = ["label_preview"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        return ["packed_at", "order_reference", "size_option", "tea_lot", "tea_grams", "amount", "organic", "label_preview"]

    @admin.display(description="Label")
    def label_preview(self, package):
        if not package.tea_lot_id:
            return "—"
        label = services.label_for(package)
        rows = [
            label.name,
            label.net_weight,
            label.grown_in,
            f"Ingredients: {label.ingredients}" if label.ingredients else "",
            label.contains,
            f"Lot {label.lot_code}",
            f"Best by {label.best_by:%Y-%m-%d}" if label.best_by else "",
            label.packer.replace("\n", ", "),
        ] + [f"Problem: {problem}" for problem in label.problems]
        return format_html_join(format_html("<br>"), "{}", ((row,) for row in rows if row))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total = services.organic_sales()
        extra_context["subtitle"] = (
            f"Organic sales this year: ${total:,.2f} of the ${settings.ORGANIC_EXEMPTION_LIMIT:,.0f} limit "
            f"(alert at ${settings.ORGANIC_SALES_ALERT:,.0f})"
        )
        return super().changelist_view(request, extra_context)

    @admin.display(description="Lot")
    def lot_link(self, package):
        if not package.tea_lot_id:
            return "—"
        return format_html('<a href="{}">{}</a>', reverse("admin:inventory_lot_change", args=[package.tea_lot_id]), package.tea_lot.code)
