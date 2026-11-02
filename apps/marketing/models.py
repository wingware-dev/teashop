"""Marketing's records: campaigns (with their public discount codes), the
idea backlog, and social posts with their approval and schedule.

Tea notes articles are the storefront's Article (drafted unpublished by the
agent), and email mailings are the email list's Mailing: marketing links
to them rather than keeping copies."""

from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils import timezone

from . import networks

ZERO = 0


class Campaign(models.Model):
    """A push the owner wants to measure: a season, a new tea, a sale.  Its
    posts carry its name in their links (utm_campaign), and its discount
    codes, which are ordinary public codes, show which orders it brought."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=60, unique=True,
        help_text="Goes in the links of its posts (utm_campaign=...), so the analytics can tell its visits apart")
    description = models.TextField(blank=True, help_text="What it is for, for you and the marketing agent")
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    codes = models.ManyToManyField(
        "checkout.DiscountCode", blank=True, related_name="campaigns",
        help_text="Public discount codes that belong to it.  The same price for everyone who uses one: codes are "
                  "never made for one person.")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-starts_on", "-pk"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("marketing:campaign", args=[self.pk])

    def clean(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValidationError({"ends_on": "The end date is before the start date."})

    def is_current(self, day=None):
        day = day or timezone.localdate()
        return (not self.starts_on or self.starts_on <= day) and (not self.ends_on or day <= self.ends_on)

    def results(self):
        """What its codes brought: paid orders, their total, the discount given."""
        from apps.checkout.models import Order

        orders = Order.objects.filter(status__in=Order.PAID_STATUSES, discount__in=self.codes.all())
        totals = orders.aggregate(orders=Count("pk"), revenue=Sum("total"), discount=Sum("discount_amount"))
        return {"orders": totals["orders"] or 0, "revenue": totals["revenue"] or ZERO,
                "discount": totals["discount"] or ZERO}


class Idea(models.Model):
    """One entry in the backlog: something worth posting or writing about,
    from the owner or suggested by the marketing agent."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        DRAFTED = "drafted", "Drafted"
        DONE = "done", "Done"
        DISMISSED = "dismissed", "Dismissed"

    OPEN = (Status.NEW, Status.DRAFTED)

    title = models.CharField(max_length=150)
    notes = models.TextField(blank=True, help_text="What you have in mind: the angle, a photo you took, a date")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW, db_index=True)
    made_by = models.CharField(max_length=80, default="owner", help_text='"owner", or the agent that suggested it')
    campaign = models.ForeignKey(Campaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="ideas")
    product = models.ForeignKey("catalog.Product", null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="+", help_text="The tea or item it is about, if one")
    articles = models.ManyToManyField("storefront.Article", blank=True, related_name="+")
    mailings = models.ManyToManyField("emaillist.Mailing", blank=True, related_name="+")
    agent_note = models.CharField(max_length=300, blank=True, editable=False,
                                  help_text="Why the assistant's last run on it saved nothing, or not everything")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("marketing:idea", args=[self.pk])

    @property
    def from_agent(self):
        return self.made_by != "owner"


class PostQuerySet(models.QuerySet):
    def waiting(self):
        return self.filter(status=Post.Status.DRAFT)

    def scheduled(self):
        return self.filter(status=Post.Status.APPROVED)


class Post(models.Model):
    """One post for one network.  The owner approves what, where and when
    together: changing any of them after approval takes it back to a
    draft.  Nothing is posted without that approval."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Waiting for your approval"
        APPROVED = "approved", "Approved and scheduled"
        DUE = "due", "Time for you to post it"
        POSTED = "posted", "Posted"
        FAILED = "failed", "Posting failed"
        REJECTED = "rejected", "Rejected"

    network = models.CharField(max_length=12, choices=networks.CHOICES)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True,
                              editable=False)
    text = models.TextField()
    title = models.CharField(max_length=100, blank=True, help_text="Pinterest only: the pin's title")
    link = models.CharField(
        max_length=300, blank=True,
        help_text="A page of the shop, as its path (/products/assam-second-flush/).  Tracking words for the "
                  "analytics are added to it.")
    photo = models.ForeignKey("catalog.ProductPhoto", null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="+", help_text="One of your product photos")
    gift = models.BooleanField(
        "shows a free gift", default=False,
        help_text="Tick when the post is about a product we gave someone free (a reviewer, an influencer, a "
                  "giveaway winner).  The text must then say so (#gifted, \"sent to them free\"): the FTC "
                  "requires the disclosure.")
    scheduled_for = models.DateTimeField(null=True, blank=True, db_index=True)
    idea = models.ForeignKey(Idea, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
    campaign = models.ForeignKey(Campaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
    product = models.ForeignKey("catalog.Product", null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="+")
    made_by = models.CharField(max_length=80, default="owner")
    edited_by_owner = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    approved_at = models.DateTimeField(null=True, blank=True, editable=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+", editable=False)
    posted_at = models.DateTimeField(null=True, blank=True, editable=False)
    external_id = models.CharField(max_length=300, blank=True, editable=False)
    external_url = models.URLField(max_length=500, blank=True)
    error = models.CharField(max_length=500, blank=True, editable=False)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["scheduled_for", "pk"]

    def __str__(self):
        return f"{self.get_network_display()} post {self.pk}"

    def get_absolute_url(self):
        return reverse("marketing:post", args=[self.pk])

    @property
    def spec(self):
        return networks.get(self.network)

    @property
    def from_agent(self):
        return self.made_by != "owner"

    @property
    def is_live(self):
        """Posted through the network's API (else the owner posts it)."""
        from . import publishers

        return publishers.posts_live(self.network)

    def tracked_link(self):
        """The link with the analytics' campaign words (UTM), absolute."""
        if not self.link:
            return ""
        path = self.link
        site = settings.SITE_URL.rstrip("/")
        if path.startswith(site):
            path = path[len(site):] or "/"
        params = urlencode({"utm_source": self.network, "utm_medium": "social",
                            "utm_campaign": self.campaign.slug if self.campaign_id else "social",
                            "utm_content": f"post-{self.pk}" if self.pk else "post"})
        return f"{site}{path}{'&' if '?' in path else '?'}{params}"

    def final_text(self):
        """What goes out: the text, with the link added for networks that
        show links in the text."""
        link = self.tracked_link()
        if link and self.spec.link_in_text and link not in self.text:
            return f"{self.text.rstrip()}\n{link}"
        return self.text

    def length(self):
        return self.spec.length(self.final_text())

    def clean_link(self):
        """The link as a shop path, or a ValidationError."""
        link = (self.link or "").strip()
        if not link:
            return ""
        site = settings.SITE_URL.rstrip("/")
        if link.startswith(site):
            link = link[len(site):] or "/"
        parts = urlsplit(link)
        if parts.scheme or parts.netloc or not link.startswith("/"):
            raise ValidationError({"link": "Link only to the shop's own pages, as a path such as /teas/."})
        return link

    def clean(self):
        self.link = self.clean_link()
