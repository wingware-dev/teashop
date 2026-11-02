from django.contrib import admin

from . import queue
from .models import Job, Schedule


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["created_at", "short_name", "status", "attempts", "max_attempts", "run_at", "finished_at"]
    list_filter = ["status", "name"]
    search_fields = ["name", "key", "last_error"]
    actions = ["run_again"]
    readonly_fields = [field.name for field in Job._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Job")
    def short_name(self, obj):
        return obj.short_name

    @admin.action(description="Run again")
    def run_again(self, request, queryset):
        count = queue.retry_now(queryset)
        self.message_user(request, f"Queued {count} failed job{'s' if count != 1 else ''} again.")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["name", "spec", "last_run_at", "next_run_at"]
    readonly_fields = ["name", "spec", "last_run_at", "next_run_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
