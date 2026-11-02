"""Approval, the schedule and posting: by hand, and through the networks'
APIs (mocked: no test reaches a real network)."""

from datetime import timedelta
from decimal import Decimal
from unittest import mock

import requests
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps import jobs
from apps.audit import acting_as_agent
from apps.checkout.models import DiscountCode, Order
from apps.core.testing import make_owner
from apps.fulfillment.testing import paid_order, size
from apps.marketing import alerts, publishers, services
from apps.marketing.jobs import weekly_ideas
from apps.marketing.models import Campaign, Idea, Post

from .helpers import MARKETING_SETTINGS, TempMedia, catalog, photo, tomorrow


def response(status=200, json=None, text=""):
    reply = mock.Mock(status_code=status, text=text or str(json))
    reply.json.return_value = json if json is not None else {}
    return reply


@override_settings(**MARKETING_SETTINGS)
class ApprovalTests(TestCase):
    def setUp(self):
        self.assam = catalog()
        self.owner, _ = make_owner()
        self.post = services.new_post(network="x", text="Assam Second Flush: malty and brisk.",
                                      link="/products/assam-second-flush/", scheduled_for=tomorrow(),
                                      made_by="marketing-agent")

    def test_owner_approves_agents_cannot(self):
        with acting_as_agent("marketing-agent"), self.assertRaises(PermissionDenied):
            services.approve(self.post, self.owner)
        services.approve(self.post, self.owner)
        self.assertEqual(self.post.status, Post.Status.APPROVED)
        self.assertEqual(self.post.approved_by, self.owner)

    def test_problems_and_past_times_block_approval(self):
        self.post.text = "This tea cures headaches."
        with self.assertRaises(ValidationError):
            services.approve(self.post, self.owner)
        self.post.text = "Malty."
        self.post.scheduled_for = timezone.now() - timedelta(hours=1)
        with self.assertRaises(ValidationError) as caught:
            services.approve(self.post, self.owner)
        self.assertIn("Its time has passed: pick a new one.", caught.exception.messages)

    def test_any_change_after_approval_needs_approval_again(self):
        services.approve(self.post, self.owner)
        self.assertTrue(services.update_post(self.post, {"scheduled_for": self.post.scheduled_for + timedelta(hours=2)},
                                             self.owner))
        self.assertEqual(self.post.status, Post.Status.DRAFT)
        self.assertIsNone(self.post.approved_by)
        self.assertFalse(self.post.edited_by_owner)
        services.update_post(self.post, {"text": "Assam: malty, brisk, lovely with milk."}, self.owner)
        self.assertTrue(self.post.edited_by_owner)
        self.assertFalse(services.update_post(self.post, {"text": self.post.text}, self.owner))

    def test_links_only_to_the_shop(self):
        self.post.link = "https://elsewhere.example/"
        with self.assertRaises(ValidationError):
            self.post.full_clean()
        self.post.link = "https://shop.example/teas/"
        self.post.full_clean()
        self.assertEqual(self.post.link, "/teas/")

    def test_by_hand_post_becomes_due_then_posted(self):
        services.approve(self.post, self.owner)
        services.publish_due(now=self.post.scheduled_for - timedelta(minutes=1))
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.Status.APPROVED)
        services.publish_due(now=self.post.scheduled_for + timedelta(minutes=1))
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.Status.DUE)
        item = next(i for i in alerts.attention_items() if i.key == f"marketing:due:{self.post.pk}")
        self.assertEqual((item.kind, item.level), ("approvals", "urgent"))
        services.mark_posted(self.post, self.owner, "https://x.com/teashop/status/1")
        self.assertEqual(self.post.status, Post.Status.POSTED)
        self.assertFalse([i for i in alerts.attention_items() if i.key.startswith("marketing:due")])

    def test_drafts_on_the_dashboard(self):
        self.post.scheduled_for = timezone.now() + timedelta(days=2)
        self.post.save()
        item = next(i for i in alerts.attention_items() if i.key == "marketing:drafts")
        self.assertEqual(item.kind, "approvals")
        self.assertEqual(item.level, "warning")
        self.post.scheduled_for = timezone.now() + timedelta(hours=3)
        self.post.save()
        item = next(i for i in alerts.attention_items() if i.key == "marketing:drafts")
        self.assertEqual(item.level, "urgent")


@override_settings(**dict(MARKETING_SETTINGS, MARKETING_POST_LIVE=["bluesky", "facebook", "instagram", "pinterest"]))
class LivePostingTests(TestCase):
    def setUp(self):
        self.assam = catalog()
        self.owner, _ = make_owner()
        self.media = TempMedia().__enter__()
        self.addCleanup(self.media.__exit__)

    def approved(self, network="bluesky", **fields):
        fields.setdefault("link", "/products/assam-second-flush/")
        post = services.new_post(network=network, text=fields.pop("text", "Assam Second Flush: malty and brisk."),
                                 scheduled_for=tomorrow(), **fields)
        services.approve(post, self.owner)
        return post

    def make_due(self, *posts, ago=timedelta(minutes=1)):
        """Move approved posts' time to just past (the jobs use the real clock)."""
        Post.objects.filter(pk__in=[p.pk for p in posts]).update(scheduled_for=timezone.now() - ago)
        for post in posts:
            post.refresh_from_db()

    @mock.patch("apps.marketing.publishers.requests.post")
    def test_bluesky(self, post_mock):
        post = self.approved("bluesky", photo=photo(self.assam))
        post_mock.side_effect = [
            response(json={"accessJwt": "jwt", "did": "did:plc:abc", "handle": "teashop.example"}),
            response(json={"blob": {"$type": "blob", "ref": {"$link": "bafy"}}}),
            response(json={"uri": "at://did:plc:abc/app.bsky.feed.post/3kxyz", "cid": "c"}),
        ]
        self.make_due(post)
        services.publish_due()
        post.refresh_from_db()
        self.assertEqual(post.status, Post.Status.POSTED, post.error)
        self.assertEqual(post.external_url, "https://bsky.app/profile/teashop.example/post/3kxyz")
        record = post_mock.call_args_list[2].kwargs["json"]["record"]
        self.assertIn("utm_source=bluesky", record["text"])
        facet = record["facets"][0]
        start, end = facet["index"]["byteStart"], facet["index"]["byteEnd"]
        self.assertEqual(record["text"].encode()[start:end].decode(), facet["features"][0]["uri"])
        self.assertEqual(record["embed"]["images"][0]["alt"], "Dark twisted leaves in an open tin")
        self.assertLessEqual(len(post_mock.call_args_list[1].kwargs["data"]), publishers.BLUESKY_MAX_IMAGE)

    @mock.patch("apps.marketing.publishers.requests.post")
    def test_instagram_and_pinterest_use_the_photos_public_url(self, post_mock):
        picture = photo(self.assam)
        instagram = self.approved("instagram", photo=picture, link="")
        pin = self.approved("pinterest", photo=picture, title="Assam Second Flush")
        post_mock.side_effect = [response(json={"id": "container-1"}), response(json={"id": "ig-1"}),
                                 response(json={"id": "pin-1"})]
        self.make_due(instagram)
        Post.objects.filter(pk=pin.pk).update(scheduled_for=instagram.scheduled_for + timedelta(seconds=1))
        services.publish_due()
        instagram.refresh_from_db()
        pin.refresh_from_db()
        self.assertEqual((instagram.status, instagram.external_id), (Post.Status.POSTED, "ig-1"))
        self.assertEqual(pin.external_url, "https://www.pinterest.com/pin/pin-1/")
        media = post_mock.call_args_list[0].kwargs["data"]
        self.assertTrue(media["image_url"].startswith("https://shop.example/"))
        self.assertTrue(post_mock.call_args_list[0].args[0].endswith("/v23.0/5678/media"))
        body = post_mock.call_args_list[2].kwargs["json"]
        self.assertEqual(body["board_id"], "board-1")
        self.assertIn("utm_source=pinterest", body["link"])

    @mock.patch("apps.marketing.publishers.requests.post")
    def test_facebook_link_post(self, post_mock):
        post = self.approved("facebook")
        post_mock.return_value = response(json={"id": "1234_99"})
        self.make_due(post)
        services.publish_due()
        post.refresh_from_db()
        self.assertEqual(post.external_url, "https://www.facebook.com/1234_99")
        data = post_mock.call_args.kwargs["data"]
        self.assertIn("utm_source=facebook", data["link"])
        self.assertEqual(data["access_token"], "page-token")

    @override_settings(JOBS_EAGER=False)
    @mock.patch("apps.marketing.publishers.requests.post")
    def test_network_down_retries_then_fails_after_the_grace(self, post_mock):
        post = self.approved("facebook")
        post_mock.side_effect = requests.ConnectionError("down")
        self.make_due(post)
        with self.assertRaises(jobs.Retry):
            services.publish(post.pk)
        post.refresh_from_db()
        self.assertEqual(post.status, Post.Status.APPROVED)
        services.publish(post.pk, now=post.scheduled_for + timedelta(hours=7))
        post.refresh_from_db()
        self.assertEqual(post.status, Post.Status.FAILED)
        item = next(i for i in alerts.attention_items() if i.key == f"marketing:failed:{post.pk}")
        self.assertEqual(item.kind, "problems")

    @mock.patch("apps.marketing.publishers.requests.post")
    def test_refused_or_unknown_outcome_fails_without_retrying(self, post_mock):
        refused = self.approved("facebook")
        post_mock.return_value = response(400, text='{"error": "token expired"}')
        self.make_due(refused)
        services.publish(refused.pk)
        refused.refresh_from_db()
        self.assertEqual(refused.status, Post.Status.FAILED)
        self.assertIn("token expired", refused.error)
        timed_out = self.approved("facebook")
        post_mock.side_effect = requests.Timeout("slow")
        self.make_due(timed_out)
        services.publish(timed_out.pk)
        timed_out.refresh_from_db()
        self.assertIn("check whether the post went up", timed_out.error)

    @mock.patch("apps.marketing.publishers.requests.post")
    def test_stale_and_withdrawn_posts_dont_go(self, post_mock):
        stale = self.approved("facebook")
        self.make_due(stale, ago=timedelta(hours=7))
        services.publish_due()
        stale.refresh_from_db()
        self.assertEqual(stale.status, Post.Status.FAILED)
        withdrawn = self.approved("facebook")
        services.withdraw(withdrawn, self.owner)
        self.make_due(withdrawn)
        services.publish(withdrawn.pk)
        post_mock.assert_not_called()
        # The owner can send a failed one again at once.
        post_mock.return_value = response(json={"id": "1234_7"})
        services.try_again(stale, self.owner)
        stale.refresh_from_db()
        self.assertEqual(stale.status, Post.Status.POSTED)

    def test_x_and_tiktok_are_always_by_hand(self):
        self.assertFalse(publishers.posts_live("x"))
        self.assertFalse(publishers.posts_live("tiktok"))
        self.assertTrue(publishers.posts_live("bluesky"))


class SettingsCheckTests(TestCase):
    @override_settings(MARKETING_POST_LIVE=["x", "bluesky"], BLUESKY_HANDLE="", BLUESKY_APP_PASSWORD="")
    def test_check(self):
        errors = publishers.check_settings()
        self.assertEqual([e.id for e in errors], ["marketing.E001", "marketing.E002"])
        self.assertIn("charges", errors[0].msg)

    @override_settings(MARKETING_POST_LIVE=[])
    def test_nothing_live_is_fine(self):
        self.assertEqual(publishers.check_settings(), [])


@override_settings(**MARKETING_SETTINGS)
class CampaignAndJobTests(TestCase):
    def setUp(self):
        catalog()

    def test_results_count_paid_orders_with_its_codes(self):
        code = DiscountCode.objects.create(code="SPRING5", kind=DiscountCode.Kind.AMOUNT, value=Decimal("5"))
        campaign = Campaign.objects.create(name="Spring", slug="spring")
        campaign.codes.add(code)
        order = paid_order([(size("assam-second-flush"), 2)])
        Order.objects.filter(pk=order.pk).update(discount=code, discount_code="SPRING5", discount_amount=Decimal("5"))
        paid_order([(size("assam-second-flush"), 1)], email="bob@example.com")
        results = campaign.results()
        self.assertEqual(results["orders"], 1)
        self.assertEqual(results["discount"], Decimal("5"))
        self.assertEqual(results["revenue"], order.total)

    def test_weekly_ideas_only_when_due(self):
        weekly_ideas()
        made = Idea.objects.exclude(made_by="owner").count()
        self.assertTrue(made)
        weekly_ideas()
        self.assertEqual(Idea.objects.exclude(made_by="owner").count(), made)

    def test_schedules_are_declared(self):
        from apps.jobs.queue import schedules

        names = {schedule.name for schedule in schedules()}
        self.assertIn("apps.marketing.jobs.publish_due_posts", names)
        self.assertIn("apps.marketing.jobs.weekly_ideas", names)

    def test_no_missing_migrations(self):
        call_command("makemigrations", "marketing", "--check", "--dry-run", verbosity=0)
