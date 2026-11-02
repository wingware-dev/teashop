"""Storefront content beyond the catalog: per-tea page variants, which AI
agents propose and the owner approves, and the tea info and history
articles."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from apps.audit import record
from apps.catalog import copy_rules
from apps.catalog.models import Product
from apps.core.design import LAYOUTS, MOTIFS, PALETTES


class PageVariantQuerySet(models.QuerySet):
    def waiting(self):
        return self.filter(status=PageVariant.Status.DRAFT)

    def live(self):
        return self.filter(status=PageVariant.Status.LIVE)


class PageVariant(models.Model):
    """One design for one product's page, within the common theme: its
    palette, motif and layout come from the design system's named choices
    (apps/core/design.py), and its headline and story are checked like
    all product copy.  An AI agent (or the owner) proposes it as a draft;
    nothing reaches customers until the owner approves it, which retires
    the product's previous live variant."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Waiting for approval"
        LIVE = "live", "Live"
        REJECTED = "rejected", "Rejected"
        RETIRED = "retired", "Replaced by a newer variant"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="page_variants")
    palette = models.CharField(max_length=20, choices=PALETTES)
    motif = models.CharField(max_length=20, choices=MOTIFS)
    layout = models.CharField(max_length=20, choices=LAYOUTS, default="classic")
    headline = models.CharField(max_length=120, blank=True, help_text="A line under the tea's name")
    story = models.TextField(blank=True, help_text="Shown above the description: a few sentences, no health claims")
    made_by = models.CharField(max_length=80, help_text='Who proposed it, e.g. "design-agent" or "owner"')
    rationale = models.TextField(blank=True, help_text="Why this design suits the tea, for the owner")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    decided_at = models.DateTimeField(null=True, blank=True, editable=False)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, editable=False, related_name="+"
    )
    decision_note = models.CharField(max_length=300, blank=True)

    objects = PageVariantQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"], condition=models.Q(status="live"), name="storefront_one_live_variant_per_product"
            )
        ]

    def __str__(self):
        return f"{self.product} variant {self.pk} ({self.get_status_display().lower()})"

    def get_absolute_url(self):
        return reverse("storefront:variant_preview", args=[self.pk])

    def copy_problems(self):
        errors = {}
        product = self.product
        for name in ("headline", "story", "rationale"):
            text = getattr(self, name)
            where = self._meta.get_field(name).verbose_name.capitalize()
            problems = copy_rules.health_claim_problems(text, where)
            if name != "rationale":  # the rationale is only for the owner
                problems += copy_rules.caffeine_free_problems(text, product.caffeine == Product.Caffeine.NONE, where)
                problems += copy_rules.origin_problems(text, product.origin_certified, where)
                problems += copy_rules.organic_problems(text, product.sold_as_organic, where)
            if problems:
                errors[name] = problems
        return errors

    def clean(self):
        if self.product_id:
            errors = self.copy_problems()
            if errors:
                raise ValidationError(errors)

    @transaction.atomic
    def approve(self, user, note=""):
        """Make this the product's live design (the owner's decision)."""
        if self.status not in (self.Status.DRAFT, self.Status.RETIRED, self.Status.REJECTED):
            raise ValidationError("Only a draft, rejected or replaced variant can be approved.")
        self.full_clean()
        now = timezone.now()
        for old in PageVariant.objects.select_for_update().filter(product=self.product, status=self.Status.LIVE):
            old.status = self.Status.RETIRED
            old.save(update_fields=["status"])
        self.status, self.decided_at, self.decided_by, self.decision_note = self.Status.LIVE, now, user, note
        self.save(update_fields=["status", "decided_at", "decided_by", "decision_note"])
        record("storefront.variant_approved", obj=self, message=f"Approved for {self.product}: {note}".strip(": "))

    @transaction.atomic
    def reject(self, user, note=""):
        if self.status != self.Status.DRAFT:
            raise ValidationError("Only a variant waiting for approval can be rejected.")
        self.status, self.decided_at, self.decided_by, self.decision_note = self.Status.REJECTED, timezone.now(), user, note
        self.save(update_fields=["status", "decided_at", "decided_by", "decision_note"])
        record("storefront.variant_rejected", obj=self, message=note)

    @transaction.atomic
    def take_down(self, user, note=""):
        """Stop showing a live variant; the page goes back to the default design."""
        if self.status != self.Status.LIVE:
            raise ValidationError("Only the live variant can be taken down.")
        self.status, self.decided_at, self.decided_by, self.decision_note = self.Status.RETIRED, timezone.now(), user, note
        self.save(update_fields=["status", "decided_at", "decided_by", "decision_note"])
        record("storefront.variant_taken_down", obj=self, message=note)


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True, published_on__lte=timezone.localdate())


class Article(models.Model):
    """A page in the tea info and history section.  The owner writes it, or
    the marketing agent drafts it (unpublished) for the owner to publish.

    The body is plain text: paragraphs separated by a blank line, and a
    line starting with "## " is a subheading."""

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    summary = models.CharField(max_length=250, help_text="For the list of articles and the page description")
    body = models.TextField(help_text='Paragraphs separated by a blank line; "## " starts a subheading')
    motif = models.CharField(max_length=20, choices=MOTIFS, default="leaf")
    palette = models.CharField(max_length=20, choices=PALETTES, default="moss")
    related_products = models.ManyToManyField(Product, blank=True, related_name="articles")
    written_by = models.CharField(max_length=80, default="owner", help_text='"owner", or the agent that drafted it')
    is_published = models.BooleanField(default=False, help_text="Shown in the shop from the publish date")
    published_on = models.DateField(default=timezone.localdate)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = ["-published_on", "-pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("storefront:article", args=[self.slug])

    def clean(self):
        errors = {}
        for name in ("title", "summary", "body"):
            problems = copy_rules.health_claim_problems(getattr(self, name), name.capitalize())
            if problems:
                errors[name] = problems
        if errors:
            raise ValidationError(errors)
