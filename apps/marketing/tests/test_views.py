"""The owner's marketing pages (signed in with two-factor), and the
analytics script on the shop's pages."""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.testing import login_verified, make_owner
from apps.marketing import services
from apps.marketing.forms import LOCAL_FORMAT
from apps.marketing.models import Campaign, Idea, Post

from .helpers import MARKETING_SETTINGS, catalog, tomorrow


@override_settings(**MARKETING_SETTINGS)
class OwnerPageTests(TestCase):
    def setUp(self):
        self.assam = catalog()
        self.owner, device = make_owner()
        login_verified(self.client, self.owner, device)

    def test_pages_need_the_owner(self):
        self.client.logout()
        response = self.client.get(reverse("marketing:home"))
        self.assertEqual(response.status_code, 302)

    def test_add_idea_draft_posts_approve(self):
        response = self.client.post(reverse("marketing:home"), {"idea-title": "Assam for autumn",
                                                                "idea-notes": "Malty mornings",
                                                                "idea-product": self.assam.pk})
        idea = Idea.objects.get(title="Assam for autumn")
        self.assertRedirects(response, idea.get_absolute_url())
        when = timezone.localtime(tomorrow()).strftime(LOCAL_FORMAT)
        response = self.client.post(reverse("marketing:idea_draft", args=[idea.pk]), {
            "task": "posts", "draft-networks": ["bluesky", "x"], "draft-when": when}, follow=True)
        self.assertContains(response, "The assistant drafted the posts below")
        posts = list(idea.posts.order_by("network"))
        self.assertEqual([p.network for p in posts], ["bluesky", "x"])
        page = self.client.get(posts[0].get_absolute_url())
        self.assertContains(page, "Approve: Bluesky")
        self.assertContains(page, "utm_source=bluesky")
        response = self.client.post(posts[0].get_absolute_url(), {"action": "approve"}, follow=True)
        self.assertContains(response, "comes to your dashboard to post")
        posts[0].refresh_from_db()
        self.assertEqual(posts[0].status, Post.Status.APPROVED)
        calendar = self.client.get(reverse("marketing:calendar"), {"month": tomorrow().strftime("%Y-%m")})
        self.assertContains(calendar, posts[0].get_absolute_url())

    def test_blocked_post_shows_problems_and_no_approve_button(self):
        post = services.new_post(network="bluesky", text="This tea heals your gut.", scheduled_for=tomorrow())
        page = self.client.get(post.get_absolute_url())
        self.assertContains(page, "Fix before approving")
        self.assertNotContains(page, "Approve: Bluesky")
        self.client.post(post.get_absolute_url(), {"action": "approve"})
        post.refresh_from_db()
        self.assertEqual(post.status, Post.Status.DRAFT)

    def test_edit_approved_post_back_to_draft(self):
        post = services.new_post(network="facebook", text="Assam: malty.", scheduled_for=tomorrow())
        services.approve(post, self.owner)
        response = self.client.post(post.get_absolute_url(), {
            "action": "save", "network": "facebook", "text": "Assam: malty and brisk.",
            "scheduled_for": timezone.localtime(post.scheduled_for).strftime(LOCAL_FORMAT)}, follow=True)
        self.assertContains(response, "It is a draft again")
        post.refresh_from_db()
        self.assertEqual((post.status, post.text, post.edited_by_owner), (Post.Status.DRAFT, "Assam: malty and brisk.",
                                                                          False))

    def test_due_post_marked_posted(self):
        post = services.new_post(network="x", text="Assam: malty.", scheduled_for=timezone.now() + timedelta(minutes=1))
        services.approve(post, self.owner)
        Post.objects.filter(pk=post.pk).update(scheduled_for=timezone.now() - timedelta(minutes=1))
        services.publish_due()
        home = self.client.get(reverse("marketing:home"))
        self.assertContains(home, "Post it now: X")
        self.client.post(post.get_absolute_url(), {"action": "posted", "url": "https://x.com/shop/status/9"})
        post.refresh_from_db()
        self.assertEqual((post.status, post.external_url), (Post.Status.POSTED, "https://x.com/shop/status/9"))

    def test_write_own_post(self):
        response = self.client.post(reverse("marketing:post_new"), {
            "network": "bluesky", "text": "Fresh Assam is in.", "link": "/products/assam-second-flush/",
            "scheduled_for": timezone.localtime(tomorrow()).strftime(LOCAL_FORMAT)})
        post = Post.objects.get()
        self.assertRedirects(response, post.get_absolute_url())
        self.assertEqual(post.made_by, "owner")

    def test_article_draft_and_publish(self):
        idea = services.add_idea("Assam", product=self.assam)
        self.client.post(reverse("marketing:idea_draft", args=[idea.pk]), {"task": "article"})
        article = idea.articles.get()
        page = self.client.get(reverse("marketing:article", args=[article.pk]))
        self.assertContains(page, "Brewing it")
        self.client.post(reverse("marketing:article", args=[article.pk]),
                         {"action": "publish", "day": timezone.localdate().isoformat()})
        article.refresh_from_db()
        self.assertTrue(article.is_published)
        self.assertEqual(self.client.get(article.get_absolute_url()).status_code, 200)

    def test_campaigns(self):
        response = self.client.post(reverse("marketing:campaigns"), {"name": "Autumn", "slug": "autumn"})
        campaign = Campaign.objects.get()
        self.assertRedirects(response, campaign.get_absolute_url())
        self.assertContains(self.client.get(campaign.get_absolute_url()), "utm_campaign")

    def test_suggest_ideas(self):
        response = self.client.post(reverse("marketing:suggest"), follow=True)
        self.assertContains(response, "The assistant suggested ideas")
        self.assertTrue(Idea.objects.exclude(made_by="owner").exists())

    def test_dashboard_shortcut_and_queue(self):
        services.new_post(network="x", text="Assam: malty.", scheduled_for=tomorrow())
        response = self.client.get(reverse("core:owner_dashboard"))
        self.assertContains(response, "Posts waiting for your approval: 1")
        self.assertContains(response, reverse("marketing:home"))


@override_settings(**dict(MARKETING_SETTINGS, ANALYTICS="plausible", ANALYTICS_SITE_ID="shop.example",
                          ANALYTICS_SCRIPT_URL="https://plausible.io/js/script.js"))
class AnalyticsTests(TestCase):
    def setUp(self):
        catalog()

    def test_script_on_catalog_pages_only(self):
        home = self.client.get(reverse("storefront:home"))
        self.assertContains(home, 'data-domain="shop.example" src="https://plausible.io/js/script.js"')
        cart = self.client.get(reverse("checkout:cart"))
        self.assertNotContains(cart, "plausible.io")
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        self.assertNotContains(self.client.get(reverse("marketing:home")), "plausible.io/js")

    @override_settings(ANALYTICS="umami", ANALYTICS_SITE_ID="abc-123", ANALYTICS_SCRIPT_URL="https://stats.example/s.js")
    def test_umami(self):
        self.assertContains(self.client.get(reverse("storefront:home")),
                            'data-website-id="abc-123" data-do-not-track="true" src="https://stats.example/s.js"')

    @override_settings(ANALYTICS="")
    def test_off(self):
        self.assertNotContains(self.client.get(reverse("storefront:home")), "data-domain")
