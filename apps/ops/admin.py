from django.contrib import admin

from .models import Proposal, QuarterlyReview, ServerReport


@admin.register(ServerReport)
class ServerReportAdmin(admin.ModelAdmin):
    list_display = ("created_at", "kind", "ok", "summary")
    list_filter = ("kind", "ok")
    readonly_fields = [field.name for field in ServerReport._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ("created_at", "title", "risk", "status", "decided_at")
    list_filter = ("status", "risk")
    readonly_fields = ("key", "title", "reason", "steps", "risk", "proposed_by", "after_reading_logs", "created_at",
                       "decided_at", "decided_by")

    def has_add_permission(self, request):
        return False


@admin.register(QuarterlyReview)
class QuarterlyReviewAdmin(admin.ModelAdmin):
    list_display = ("quarter", "completed_at", "completed_by")
    readonly_fields = ("quarter", "completed_at", "completed_by", "checked", "facts")

    def has_add_permission(self, request):
        return False
