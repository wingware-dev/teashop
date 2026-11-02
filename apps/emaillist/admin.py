from django.contrib import admin, messages

from . import services
from .models import ConsentEvent, Delivery, Mailing, Subscriber


class ConsentEventInline(admin.TabularInline):
    model = ConsentEvent
    extra = 0
    can_delete = False
    fields = ["at", "action", "method", "email", "frequency", "ip_address", "user_agent", "wording"]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "status", "frequency", "confirmed_at", "last_mailed_on", "unsubscribed_at"]
    list_filter = ["status", "frequency"]
    search_fields = ["email"]
    readonly_fields = ["email", "status", "frequency", "created_at", "requested_at", "confirmation_sent_at",
                       "confirmed_at", "unsubscribed_at", "last_mailed_on"]
    inlines = [ConsentEventInline]
    actions = ["remove_from_list"]

    def has_add_permission(self, request):
        # People join only through the sign-up form and its confirmation.
        return False

    def has_delete_permission(self, request, obj=None):
        # Keep the consent records; take people off with the action instead.
        return False

    @admin.action(description="Take off the list (asked by email, bounced, complained)")
    def remove_from_list(self, request, queryset):
        removed = sum(services.unsubscribe(s, ConsentEvent.Method.OWNER, user=request.user) for s in queryset)
        self.message_user(request, f"Took {removed} off the list.", messages.SUCCESS)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ["subject", "status", "created_by", "created_at", "approved_at", "send_until"]
    list_filter = ["status"]
    readonly_fields = ["status", "created_at", "created_by", "approved_at", "approved_by", "withdrawn_at"]

    def has_change_permission(self, request, obj=None):
        # Drafts are written and approved on the owner's email list pages.
        return False


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ["subscriber", "subject", "created_at", "sent_at", "skipped_at"]
    list_filter = ["sent_at", "skipped_at"]
    search_fields = ["subscriber__email", "subject"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
