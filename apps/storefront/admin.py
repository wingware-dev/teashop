from django.contrib import admin
from django.utils.html import format_html

from .models import Article, PageVariant


@admin.register(PageVariant)
class PageVariantAdmin(admin.ModelAdmin):
    """Variants are approved or rejected on their preview page, which shows
    them as customers would see them; here they can be listed and edited
    while still drafts."""

    list_display = ["product", "status", "palette", "motif", "layout", "made_by", "created_at", "preview_link"]
    list_filter = ["status", "palette", "motif", "layout"]
    search_fields = ["product__name", "headline", "made_by"]
    autocomplete_fields = ["product"]
    readonly_fields = ["status", "created_at", "decided_at", "decided_by", "preview_link"]
    fields = ["product", "palette", "motif", "layout", "headline", "story", "made_by", "rationale", "decision_note",
              *readonly_fields]

    def has_change_permission(self, request, obj=None):
        # A live or decided design is changed by proposing a new one, so
        # what was approved is what customers see.
        if obj is not None and obj.status != PageVariant.Status.DRAFT:
            return False
        return super().has_change_permission(request, obj)

    @admin.display(description="Preview, approve or reject")
    def preview_link(self, variant):
        if not variant.pk:
            return "—"
        return format_html('<a href="{}">Open preview</a>', variant.get_absolute_url())


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "is_published", "published_on", "written_by"]
    list_filter = ["is_published", "written_by"]
    search_fields = ["title", "summary", "body"]
    prepopulated_fields = {"slug": ["title"]}
    filter_horizontal = ["related_products"]
    fields = ["title", "slug", "summary", "body", "related_products", "motif", "palette", "written_by",
              "is_published", "published_on"]
