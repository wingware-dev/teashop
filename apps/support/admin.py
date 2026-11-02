from django.contrib import admin

from .models import Conversation, Draft, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    can_delete = False
    fields = ["created_at", "sender", "body", "emailed_at", "handled_at"]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """For looking things up; the owner answers on the support pages."""

    list_display = ["last_activity_at", "channel", "email", "subject", "status", "category"]
    list_filter = ["status", "channel", "category"]
    search_fields = ["email", "subject", "name"]
    readonly_fields = ["channel", "email", "name", "subject", "order", "status", "category", "escalated_at",
                       "escalation_reason", "created_at", "last_activity_at"]
    inlines = [MessageInline]

    def has_add_permission(self, request):
        return False


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ["created_at", "conversation", "category", "status", "similarity", "approved"]
    list_filter = ["status", "category", "approved"]
    readonly_fields = ["conversation", "category", "body", "status", "sent_body", "similarity", "approved",
                       "created_at", "decided_at"]

    def has_add_permission(self, request):
        return False
