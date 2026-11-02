from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q, Sum
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from . import services, tracing
from .reorder import reorders
from .models import (
    Allergen,
    BlendBatch,
    BlendInput,
    Item,
    Lot,
    LotDocument,
    PurchaseOrder,
    PurchaseOrderLine,
    Receipt,
    Recipe,
    RecipeComponent,
    StockAdjustment,
    StockMovement,
    Supplier,
)

USABLE = Q(lots__status=Lot.Status.ACTIVE, lots__quantity_on_hand__gt=0)


class ReadOnlyInlineMixin:
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_name", "email", "phone", "lead_time_days", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "contact_name", "email"]


class StockLevelFilter(admin.SimpleListFilter):
    title = "stock"
    parameter_name = "stock"

    def lookups(self, request, model_admin):
        return [("low", "At or below reorder level"), ("out", "None usable")]

    def queryset(self, request, queryset):
        if self.value() == "low":
            return queryset.filter(pk__in=[r.item.pk for r in reorders() if r.is_low])
        if self.value() == "out":
            return queryset.filter(usable_on_hand=0)
        return queryset


class ItemLotInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = Lot
    fields = ["code", "status", "received_on", "best_by", "on_hand", "supplier"]
    readonly_fields = fields
    verbose_name_plural = "Lots with stock"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(quantity_on_hand__gt=0).select_related("item", "supplier")

    @admin.display(description="On hand")
    def on_hand(self, lot):
        return lot.format_quantity(lot.quantity_on_hand)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_filter = [StockLevelFilter, "kind", "is_active"]
    search_fields = ["name", "code", "ingredient_name"]
    autocomplete_fields = ["default_supplier"]
    inlines = [ItemLotInline]
    fieldsets = [
        (None, {"fields": ["name", "code", "kind", "ingredient_name", "default_supplier", "is_active"]}),
        ("Reordering", {"fields": ["auto_reorder", "reorder_level", "safety_days", "cover_days", "minimum_order"]}),
        (None, {"fields": ["notes"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(usable_on_hand=Sum("lots__quantity_on_hand", filter=USABLE, default=0))

    def get_list_display(self, request):
        # Reorder levels are worked out for all items at once (reorder.py),
        # not per row.
        info = {r.item.pk: r for r in reorders()}

        @admin.display(description="Reorder level")
        def reorder_level_display(item):
            r = info.get(item.pk)
            if not r or not r.level:
                return "—"
            return item.format_quantity(r.level) + (" (auto)" if r.level > item.reorder_level else "")

        @admin.display(description="Low", boolean=True)
        def low(item):
            r = info.get(item.pk)
            return bool(r and r.is_low)

        return ["name", "code", "kind", "on_hand", reorder_level_display, low, "is_active"]

    @admin.display(description="Usable stock", ordering="usable_on_hand")
    def on_hand(self, item):
        return item.format_quantity(item.usable_on_hand)


class LotDocumentInline(admin.TabularInline):
    model = LotDocument
    extra = 1
    fields = ["kind", "file", "description", "uploaded_at"]
    readonly_fields = ["uploaded_at"]


class LotMovementInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = StockMovement
    fk_name = "lot"
    fields = ["created_at", "kind", "change", "reason", "reference", "note"]
    readonly_fields = fields
    show_change_link = False
    verbose_name_plural = "Stock movements"

    @admin.display(description="Change")
    def change(self, movement):
        sign = "+" if movement.quantity > 0 else ""
        return sign + movement.lot.format_quantity(movement.quantity)


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ["code", "item", "supplier", "received_on", "best_by", "on_hand", "status", "organic"]
    list_filter = ["status", "source", "organic", "item__kind", "supplier"]
    search_fields = ["code", "supplier_lot_code", "item__name", "item__code", "supplier__name"]
    date_hierarchy = "received_on"
    autocomplete_fields = ["item", "supplier", "receipt", "purchase_order_line"]
    filter_horizontal = ["allergens"]
    inlines = [LotDocumentInline, LotMovementInline]
    actions = ["put_on_hold", "release", "recall"]
    fieldsets = [
        (None, {"fields": ["item", "code", "source", "status", "status_note"]}),
        ("Stock", {"fields": ["quantity_received", "on_hand", "trace_link"]}),
        ("Where it came from", {"fields": ["supplier", "supplier_lot_code", "receipt", "purchase_order_line", "received_on", "harvest_year"]}),
        ("Label facts", {"fields": ["best_by", "country_of_origin", "organic", "ingredients", "allergens", "allergen_statement"]}),
        ("Cost", {"fields": ["landed_cost", "tariff_cost"]}),
        (None, {"fields": ["notes"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("item", "supplier")

    def get_readonly_fields(self, request, obj=None):
        fields = ["source", "on_hand", "trace_link"]
        if obj is not None:
            fields += ["code", "quantity_received", "receipt"]
        return fields

    @admin.display(description="On hand", ordering="quantity_on_hand")
    def on_hand(self, lot):
        return lot.format_quantity(lot.quantity_on_hand) if lot.pk else "—"

    @admin.display(description="Traceability")
    def trace_link(self, lot):
        if not lot.pk:
            return "—"
        return format_html('<a href="{}">Trace this lot (recall report)</a>', reverse("inventory:lot_trace", args=[lot.pk]))

    @admin.action(description="Put selected lots on hold (nothing is packed from them)")
    def put_on_hold(self, request, queryset):
        count = 0
        for lot in queryset.filter(status=Lot.Status.ACTIVE):
            lot.status = Lot.Status.ON_HOLD
            lot.save(update_fields=["status"])
            count += 1
        self.message_user(request, f"{count} lot(s) put on hold.")

    @admin.action(description="Release selected lots from hold")
    def release(self, request, queryset):
        count = 0
        for lot in queryset.filter(status=Lot.Status.ON_HOLD):
            lot.status = Lot.Status.ACTIVE
            lot.status_note = ""
            lot.save(update_fields=["status", "status_note"])
            count += 1
        self.message_user(request, f"{count} lot(s) released.")

    @admin.action(description="Recall selected lots and the blends made from them")
    def recall(self, request, queryset):
        for lot in queryset:
            result = tracing.recall(lot)
            orders = result.order_references()
            derived = ", ".join(d.code for d in result.derived) or "none"
            self.message_user(
                request,
                format_html(
                    'Recalled {} (blend lots: {}). {} order(s) to contact: {}. <a href="{}">Recall report</a>',
                    lot.code,
                    derived,
                    len(orders),
                    ", ".join(orders) or "none",
                    reverse("inventory:lot_trace", args=[lot.pk]),
                ),
                messages.WARNING,
            )


class ReceiptLotInline(admin.StackedInline):
    """Each line of a delivery becomes a lot.  Lots already received show
    read-only: correct them on the lot's own page or with an adjustment."""

    model = Lot
    extra = 1
    can_delete = False
    show_change_link = True
    autocomplete_fields = ["item", "purchase_order_line"]
    filter_horizontal = ["allergens"]
    fields = [
        "item",
        "purchase_order_line",
        "quantity_received",
        "supplier_lot_code",
        "harvest_year",
        "best_by",
        "country_of_origin",
        "organic",
        "allergens",
        "landed_cost",
        "tariff_cost",
    ]
    verbose_name = "lot received"
    verbose_name_plural = "Lots received in this delivery"

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ["__str__", "supplier", "purchase_order", "received_on", "lot_count"]
    list_filter = ["supplier"]
    search_fields = ["supplier__name", "purchase_order__reference", "lots__code", "notes"]
    date_hierarchy = "received_on"
    autocomplete_fields = ["supplier", "purchase_order"]
    inlines = [ReceiptLotInline]

    @admin.display(description="Lots")
    def lot_count(self, receipt):
        return receipt.lots.count()

    def save_formset(self, request, form, formset, change):
        # Lot.save() takes the supplier and date from the receipt.
        super().save_formset(request, form, formset, change)
        if form.instance.purchase_order_id:
            form.instance.purchase_order.refresh_status()


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    autocomplete_fields = ["item"]
    fields = ["item", "quantity", "unit_cost", "received", "outstanding"]
    readonly_fields = ["received", "outstanding"]

    @admin.display(description="Received")
    def received(self, line):
        return line.item.format_quantity(line.quantity_received()) if line.pk else "—"

    @admin.display(description="Still to come")
    def outstanding(self, line):
        return line.item.format_quantity(line.quantity_outstanding()) if line.pk else "—"


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Drafts (by hand or suggested from reorder levels) wait for the
    owner's approval: the "Approve and mark ordered" button, or the list
    action.  The status is never edited by hand."""

    list_display = ["__str__", "supplier", "status", "source", "ordered_on", "expected_on", "approved_by"]
    list_filter = ["status", "source", "supplier"]
    search_fields = ["reference", "supplier__name", "notes"]
    autocomplete_fields = ["supplier"]
    inlines = [PurchaseOrderLineInline]
    actions = ["approve", "cancel"]
    change_form_template = "admin/inventory/purchaseorder/change_form.html"
    fields = ["supplier", "reference", "ordered_on", "expected_on", "notes", "status", "source", "approval", "deliveries"]
    readonly_fields = ["status", "source", "approval", "deliveries"]

    @admin.display(description="Approval")
    def approval(self, order):
        if order.approved_at:
            return f"Approved by {order.approved_by or 'a removed user'} on {order.approved_at:%Y-%m-%d %H:%M}"
        if order.status == PurchaseOrder.Status.DRAFT:
            return "Not approved yet: nothing is ordered until you approve it."
        return "—"

    @admin.display(description="Deliveries")
    def deliveries(self, order):
        if not order.pk or order.status in (PurchaseOrder.Status.DRAFT, PurchaseOrder.Status.CANCELLED):
            return "—"
        receipts = format_html_join(
            ", ",
            '<a href="{}">{}</a>',
            ((reverse("admin:inventory_receipt_change", args=[r.pk]), f"{r.received_on:%Y-%m-%d}") for r in order.receipts.all()),
        )
        add = reverse("admin:inventory_receipt_add") + f"?supplier={order.supplier_id}&purchase_order={order.pk}"
        link = format_html('<a href="{}">Record a delivery for this order</a>', add)
        return format_html("{} {}", receipts, link) if receipts else link

    def approve_one(self, request, order):
        try:
            services.approve_purchase_order(order, request.user)
        except (ValidationError, PermissionDenied) as error:
            text = " ".join(error.messages) if isinstance(error, ValidationError) else str(error)
            self.message_user(request, text, messages.ERROR)
            return False
        return True

    @admin.action(description="Approve selected drafts and mark them ordered")
    def approve(self, request, queryset):
        count = sum(self.approve_one(request, order) for order in queryset)
        if count:
            self.message_user(request, f"{count} purchase order(s) approved.  Send them to the supplier.")

    @admin.action(description="Cancel selected purchase orders")
    def cancel(self, request, queryset):
        count = 0
        for order in queryset:
            try:
                services.cancel_purchase_order(order)
                count += 1
            except ValidationError as error:
                self.message_user(request, " ".join(error.messages), messages.ERROR)
        if count:
            self.message_user(request, f"{count} purchase order(s) cancelled.")

    def response_change(self, request, obj):
        if "_approve" in request.POST:
            if self.approve_one(request, obj):
                self.message_user(request, f"{obj} approved.  Send it to the supplier.")
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)


@admin.register(PurchaseOrderLine)
class PurchaseOrderLineAdmin(admin.ModelAdmin):
    """Registered for the autocomplete on lots; edit lines on their order."""

    search_fields = ["item__name", "item__code", "order__reference", "order__supplier__name"]

    def get_model_perms(self, request):
        return {}


class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        fields = ["lot", "quantity", "reason", "note"]
        help_texts = {
            "quantity": "Grams for bulk items, pieces otherwise.  Negative removes stock (loss, sample), "
            "positive adds it (a count found more).",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.kind = StockMovement.Kind.ADJUSTMENT
        self.fields["reason"].required = True

    def clean(self):
        data = super().clean()
        lot, quantity = data.get("lot"), data.get("quantity")
        if lot and quantity and lot.quantity_on_hand + quantity < 0:
            self.add_error("quantity", f"Lot {lot.code} has only {lot.format_quantity(lot.quantity_on_hand)}.")
        return data


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    form = StockAdjustmentForm
    list_display = ["created_at", "lot", "change", "reason", "note"]
    list_filter = ["reason"]
    search_fields = ["lot__code", "lot__item__name", "note"]
    date_hierarchy = "created_at"
    autocomplete_fields = ["lot"]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(kind=StockMovement.Kind.ADJUSTMENT).select_related("lot__item")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Change")
    def change(self, movement):
        sign = "+" if movement.quantity > 0 else ""
        return sign + movement.lot.format_quantity(movement.quantity)

    def save_model(self, request, obj, form, change):
        # Through the service, which locks the lot and keeps its total right.
        movement = services.adjust(obj.lot, obj.quantity, obj.reason, obj.note)
        obj.pk = movement.pk
        obj.created_at = movement.created_at
        obj._state.adding = False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Every stock change, read-only."""

    list_display = ["created_at", "lot", "kind", "change", "reason", "reference", "note"]
    list_filter = ["kind", "reason", "lot__item__kind"]
    search_fields = ["lot__code", "lot__item__name", "reference", "note"]
    date_hierarchy = "created_at"
    list_select_related = ["lot__item"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Change")
    def change(self, movement):
        sign = "+" if movement.quantity > 0 else ""
        return sign + movement.lot.format_quantity(movement.quantity)


class RecipeComponentFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE"):
                total += form.cleaned_data.get("grams_per_kg") or 0
        if any(self.errors):
            return
        if total != 1000:
            raise ValidationError(f"The components add up to {total} g per kg; they must add up to 1000.")


class RecipeComponentInline(admin.TabularInline):
    model = RecipeComponent
    formset = RecipeComponentFormSet
    extra = 3
    autocomplete_fields = ["item"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["name", "output_item", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "output_item__name"]
    autocomplete_fields = ["output_item"]
    inlines = [RecipeComponentInline]


class BlendInputFormSet(BaseInlineFormSet):
    def inputs(self):
        return [
            (form.cleaned_data["lot"], form.cleaned_data["quantity"])
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE") and form.cleaned_data.get("lot")
        ]

    def clean(self):
        super().clean()
        batch = self.instance
        if any(self.errors) or batch.pk or not batch.recipe_id or not batch.quantity_made:
            return
        inputs = self.inputs()
        if not inputs:
            inputs = services.suggest_blend_inputs(batch.recipe, batch.quantity_made)
        services.check_blend(batch, inputs)


class BlendInputInline(admin.TabularInline):
    model = BlendInput
    formset = BlendInputFormSet
    extra = 4
    autocomplete_fields = ["lot"]
    verbose_name_plural = "Ingredient lots used (leave empty to use the oldest best-by lots)"

    def has_change_permission(self, request, obj=None):
        return obj is None

    def has_add_permission(self, request, obj=None):
        return obj is None

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BlendBatch)
class BlendBatchAdmin(admin.ModelAdmin):
    """Making a blend: choose the recipe and how much was made, and the
    ingredient lots and grams actually used (or leave them for the oldest
    lots).  Saving takes the ingredients from stock and makes the blend lot."""

    list_display = ["__str__", "recipe", "made_on", "quantity_made", "output_lot_link"]
    list_filter = ["recipe"]
    search_fields = ["recipe__name", "output_lot__code", "inputs__lot__code"]
    date_hierarchy = "made_on"
    autocomplete_fields = ["recipe"]
    inlines = [BlendInputInline]

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ["output_lot_link"]
        return ["recipe", "made_on", "quantity_made", "best_by", "output_lot_link"]

    def get_fields(self, request, obj=None):
        return ["recipe", "made_on", "quantity_made", "best_by", "output_lot_link", "notes"]

    @admin.display(description="Blend lot")
    def output_lot_link(self, batch):
        if not batch.output_lot_id:
            return "—"
        return format_html(
            '<a href="{}">{}</a>', reverse("admin:inventory_lot_change", args=[batch.output_lot_id]), batch.output_lot.code
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
        # A new batch is saved in save_related, with its inputs, by make_blend().

    def save_related(self, request, form, formsets, change):
        if change:
            return super().save_related(request, form, formsets, change)
        inputs = []
        for formset in formsets:
            if isinstance(formset, BlendInputFormSet):
                inputs = formset.inputs()
            # The admin's change message reads these, which formset.save() would set.
            formset.new_objects, formset.changed_objects, formset.deleted_objects = [], [], []
        services.make_blend(form.instance, inputs or None)
