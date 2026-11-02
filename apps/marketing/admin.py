from django.contrib import admin

from .models import Campaign, Idea, Post


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "starts_on", "ends_on"]
    prepopulated_fields = {"slug": ["name"]}
    filter_horizontal = ["codes"]


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "made_by", "created_at"]
    list_filter = ["status", "made_by"]
    search_fields = ["title", "notes"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Read-only: posts are approved on the marketing pages, where the
    checks run (owner/marketing/)."""

    list_display = ["__str__", "status", "scheduled_for", "made_by", "posted_at"]
    list_filter = ["status", "network"]
    search_fields = ["text"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
