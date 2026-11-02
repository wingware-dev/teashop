"""The marketing pages in a real browser: phone and desktop, light and
dark, WCAG 2.2 AA checks, screenshots (see apps.core.uitesting).  The
flow test adds an idea, has the assistant (its stand-in) draft posts, and
approves one."""

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.uitesting import BrowserTestCase
from apps.marketing import agent, services
from apps.marketing.models import Post

from .helpers import MARKETING_SETTINGS, catalog, tomorrow


@override_settings(**MARKETING_SETTINGS)
class MarketingUITests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        self.assam = catalog()

    def drafted(self):
        idea = services.add_idea("Autumn mornings with Assam", "A cosy post with the new photo", product=self.assam)
        result = agent.draft_posts(idea, ["bluesky", "facebook", "x", "instagram"], when=tomorrow())
        services.add_idea("Teas for winter evenings", made_by=agent.AGENT)
        agent.draft_article(idea)
        return idea, result.saved

    def test_home(self):
        self.drafted()
        self.check_page(reverse("marketing:home"), "marketing-home", signed_in=True)

    def test_idea(self):
        idea, _ = self.drafted()
        self.check_page(idea.get_absolute_url(), "marketing-idea", signed_in=True)

    def test_post(self):
        _, posts = self.drafted()
        self.check_page(posts[0].get_absolute_url(), "marketing-post", signed_in=True)

    def test_blocked_post(self):
        post = services.new_post(network="instagram", text="Our tea boosts immunity.  Customers say ★★★★★",
                                 scheduled_for=tomorrow(), made_by=agent.AGENT)
        self.check_page(post.get_absolute_url(), "marketing-post-blocked", signed_in=True)

    def test_calendar(self):
        _, posts = self.drafted()
        month = timezone.localtime(posts[0].scheduled_for).strftime("%Y-%m")
        self.check_page(reverse("marketing:calendar") + f"?month={month}", "marketing-calendar", signed_in=True)

    def test_campaigns(self):
        self.check_page(reverse("marketing:campaigns"), "marketing-campaigns", signed_in=True)

    def test_article(self):
        idea, _ = self.drafted()
        self.check_page(reverse("marketing:article", args=[idea.articles.get().pk]), "marketing-article",
                        signed_in=True)

    def test_flow(self):
        page = self.new_page("desktop", "light", signed_in=True)
        page.goto(self.url(reverse("marketing:home")))
        page.get_by_label("Title").fill("Assam for chilly mornings")
        page.get_by_label("Product").select_option(label=self.assam.name)
        page.get_by_role("button", name="Add to the backlog").click()
        page.get_by_role("heading", name="Assam for chilly mornings").wait_for()
        for name in ("Instagram", "Facebook", "Pinterest", "X", "TikTok"):
            page.get_by_label(name, exact=True).uncheck()
        page.get_by_role("button", name="Draft posts").click()
        page.get_by_text("The assistant drafted the posts below").wait_for()
        self.check_current(page, "marketing-flow-drafted")
        page.get_by_role("link", name="Bluesky post").click()
        page.get_by_role("button", name="Approve: Bluesky").click()
        page.locator(".messages li.success").wait_for()
        self.check_current(page, "marketing-flow-approved")
        post = Post.objects.get(network="bluesky")
        self.assertEqual(post.status, Post.Status.APPROVED)
