from django.contrib import admin

from .models import AccountingEntry


@admin.register(AccountingEntry)
class AccountingEntryAdmin(admin.ModelAdmin):
    """Read-only, except deleting a failed day so it is worked out afresh."""

    list_display = ["day", "status", "client", "external_id", "posted_at"]
    list_filter = ["status", "client"]
    readonly_fields = [f.name for f in AccountingEntry._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return obj is not None and obj.status == AccountingEntry.Status.FAILED and super().has_delete_permission(request, obj)
