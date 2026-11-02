from django.contrib import admin

from .models import AIUsage


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    """Read-only: the record of what the agents spent."""

    list_display = ["at", "agent", "model", "live", "input_tokens", "output_tokens", "cost", "purpose"]
    list_filter = ["agent", "live", "model"]
    date_hierarchy = "at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
