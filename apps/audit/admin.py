from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """Read-only view of the audit log."""

    list_display = ["timestamp", "actor_type", "actor_label", "action", "object_type", "object_repr", "ip_address"]
    list_filter = ["actor_type", "action", "object_type"]
    search_fields = ["actor_label", "action", "object_type", "object_id", "object_repr", "message"]
    date_hierarchy = "timestamp"
    readonly_fields = [f.name for f in AuditEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
