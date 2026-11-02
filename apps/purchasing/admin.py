from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect

from apps.inventory.models import Item

from . import services
from .models import StockCount, StockCountLine


class StockCountForm(forms.ModelForm):
    kinds = forms.MultipleChoiceField(
        choices=Item.Kind.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="What to count; none ticked counts everything",
    )

    class Meta:
        model = StockCount
        fields = ["kinds", "notes"]


class StockCountLineInline(admin.TabularInline):
    model = StockCountLine
    extra = 0
    can_delete = False
    fields = ["lot", "item", "expected_display", "counted", "difference_display", "reason", "note"]
    readonly_fields = ["lot", "item", "expected_display", "difference_display"]
    verbose_name_plural = "Lots to count (weigh bulk tea in grams; leave blank what you didn't count)"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("lot__item")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is not None and obj.status == StockCount.Status.OPEN

    @admin.display(description="Item")
    def item(self, line):
        return line.lot.item

    @admin.display(description="Expected")
    def expected_display(self, line):
        return line.lot.format_quantity(line.expected)

    @admin.display(description="Difference")
    def difference_display(self, line):
        if line.difference is None:
            return "—"
        sign = "+" if line.difference > 0 else ""
        return sign + line.lot.format_quantity(line.difference)


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    """Start a count (choose what to count), enter what is on the shelf for
    each lot, then "Apply count" turns the differences into adjustments."""

    form = StockCountForm
    list_display = ["__str__", "kind_labels", "status", "line_count", "applied_at", "applied_by"]
    list_filter = ["status"]
    change_form_template = "admin/purchasing/stockcount/change_form.html"

    def get_fields(self, request, obj=None):
        if obj is None:
            return ["kinds", "notes"]
        return ["kind_labels", "status", "started_at", "applied_at", "applied_by", "notes"]

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return []
        readonly = ["kind_labels", "status", "started_at", "applied_at", "applied_by"]
        return readonly + (["notes"] if obj.status == StockCount.Status.APPLIED else [])

    def get_inlines(self, request, obj):
        return [StockCountLineInline] if obj else []

    def has_delete_permission(self, request, obj=None):
        return obj is None or obj.status == StockCount.Status.OPEN

    @admin.display(description="What is counted")
    def kind_labels(self, count):
        return count.kind_labels()

    @admin.display(description="Lots")
    def line_count(self, count):
        return count.lines.count()

    def save_model(self, request, obj, form, change):
        if change:
            return super().save_model(request, obj, form, change)
        count = services.start_count(form.cleaned_data["kinds"], form.cleaned_data["notes"])
        obj.pk = count.pk
        obj.started_at = count.started_at
        obj._state.adding = False

    def response_change(self, request, obj):
        if "_apply" in request.POST:
            try:
                movements = services.apply_count(obj, request.user)
            except (ValidationError, PermissionDenied) as error:
                text = " ".join(error.messages) if isinstance(error, ValidationError) else str(error)
                self.message_user(request, text, messages.ERROR)
            else:
                self.message_user(request, f"Count applied: {len(movements)} adjustment(s) recorded.")
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)
