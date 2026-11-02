from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse

from . import emails, orders, payments, subscriptions
from .models import (CheckoutSettings, Customer, DiscountCode, NexusThreshold, Order, OrderLine, Subscription,
                     SubscriptionPlan, TaxRate)


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    can_delete = False
    fields = ["product_name", "size_name", "sku", "kind", "quantity", "unit_price", "line_total", "discount_share",
              "taxable"]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Orders are what the customer agreed to and paid: only the tracking
    number is entered here (phase 5's fulfillment pages buy labels).
    Entering it marks the order shipped and emails the customer."""

    list_display = ["number", "status", "email", "ship_state", "total", "paid_at", "ship_by", "tracking_number"]
    list_filter = ["status", "ship_state", "tax_fallback"]
    search_fields = ["number", "email", "ship_name", "ship_zip", "tracking_number"]
    date_hierarchy = "created_at"
    inlines = [OrderLineInline]
    actions = ["resend_confirmation"]
    editable = ["carrier", "tracking_number"]
    fieldsets = [
        (None, {"fields": ["number", "status", "email", "customer", "subscription", "created_at", "paid_at",
                           "ship_by"]}),
        ("Ship to", {"fields": ["ship_name", "ship_street1", "ship_street2", "ship_city", "ship_state", "ship_zip",
                                "ship_phone", "address_verified"]}),
        ("Figures", {"fields": ["subtotal", "discount_code", "discount_amount", "shipping_service", "shipping_cost",
                                "shipping_amount", "taxable_amount", "tax_rate", "tax_jurisdiction", "tax_fallback",
                                "tax_amount", "total"]}),
        ("Payment", {"fields": ["payment_provider", "payment_id", "amount_received"]}),
        ("Shipping", {"fields": ["carrier", "tracking_number", "shipped_at", "shipping_rate_id",
                                 "shipping_shipment_id"]}),
        ("Emails", {"fields": ["confirmation_sent_at", "owner_notified_at", "shipped_email_sent_at"]}),
    ]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in Order._meta.fields if f.name not in self.editable] + ["number", "token"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        tracking = obj.tracking_number.strip()
        if "tracking_number" in form.changed_data and tracking and obj.status == Order.Status.PAID:
            orders.mark_shipped(obj, tracking, obj.carrier or "USPS")
            messages.success(request, f"Order {obj.number} marked shipped; the tracking email is on its way.")
            return
        super().save_model(request, obj, form, change)

    @admin.action(description="Send the confirmation email again")
    def resend_confirmation(self, request, queryset):
        sent = sum(1 for order in queryset.filter(status__in=Order.PAID_STATUSES) if emails.order_confirmation(order))
        self.message_user(request, f"Queued {sent} confirmation email{'s' if sent != 1 else ''} to send again.")


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "kind", "value", "min_subtotal", "starts_on", "ends_on", "max_uses", "times_used",
                    "is_active"]
    list_filter = ["kind", "is_active"]
    search_fields = ["code", "description"]

    @admin.display(description="Used")
    def times_used(self, code):
        return code.uses()


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ["state", "zip_prefix", "rate", "jurisdiction", "checked_on"]
    list_filter = ["state"]
    search_fields = ["zip_prefix", "jurisdiction"]


@admin.register(NexusThreshold)
class NexusThresholdAdmin(admin.ModelAdmin):
    list_display = ["state", "has_sales_tax", "sales", "transactions", "needs_both", "notes"]
    list_filter = ["has_sales_tax", "needs_both"]


@admin.register(CheckoutSettings)
class CheckoutSettingsAdmin(admin.ModelAdmin):
    """One row: the list page goes straight to it."""

    fieldsets = [
        ("Shipping", {"fields": ["free_shipping_over", "ship_within_days"]}),
        ("Vacation mode", {"fields": ["vacation_mode", "vacation_message", "vacation_ships_from",
                                      "vacation_pause_orders"]}),
    ]

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse("admin:checkout_checkoutsettings_change", args=[CheckoutSettings.current().pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "interval_months", "is_active", "subscribers"]
    prepopulated_fields = {"slug": ["name"]}
    fields = ["name", "slug", "description", "price", "interval_months", "is_active", "sort_order"]

    @admin.display(description="Active subscribers")
    def subscribers(self, plan):
        return plan.subscriptions.filter(status__in=Subscription.LIVE_STATUSES).count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["email", "plan", "status", "price", "current_period_end", "created_at"]
    list_filter = ["status", "plan"]
    search_fields = ["email", "ship_name"]
    actions = ["cancel_subscriptions"]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in Subscription._meta.fields] + ["token"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Cancel (no more renewals; the customer is emailed)")
    def cancel_subscriptions(self, request, queryset):
        done = 0
        for subscription in queryset:
            try:
                done += subscriptions.cancel(subscription, by=f"owner ({request.user})")
            except payments.PaymentError as exc:
                self.message_user(request, f"{subscription}: {exc}", messages.ERROR)
        self.message_user(request, f"Cancelled {done}.")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["email", "ship_name", "created_at", "last_sign_in_at"]
    search_fields = ["email", "ship_name"]
    readonly_fields = ["created_at", "last_sign_in_at"]
