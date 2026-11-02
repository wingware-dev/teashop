import json
import tempfile
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.audit.models import AuditEvent
from apps.catalog.models import Product
from apps.core import attention
from apps.core.testing import login_verified, make_owner
from apps.storefront import alerts, demo
from apps.storefront.models import PageVariant


def variant(product, **fields):
    fields.setdefault("palette", "moss")
    fields.setdefault("motif", "leaf")
    fields.setdefault("made_by", "design-agent")
    return PageVariant.objects.create(product=product, **fields)


@override_settings(STOREFRONT_OPEN=True)
class VariantWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        demo.load()

    def setUp(self):
        self.owner, device = make_owner()
        login_verified(self.client, self.owner, device)
        self.product = Product.objects.get(slug="sencha-morning-mist")

    def test_draft_is_not_shown_to_customers(self):
        variant(self.product, palette="poppy", headline="A new look")
        self.client.logout()
        response = self.client.get(self.product.get_absolute_url())
        self.assertNotContains(response, "A new look")
        self.assertNotContains(response, "palette-poppy layout")

    def test_approving_makes_it_live_and_retires_the_old_one(self):
        first = variant(self.product, palette="poppy", headline="First look")
        first.approve(self.owner)
        second = variant(self.product, palette="plum", layout="wide", headline="Second look")
        second.approve(self.owner, "Better")
        first.refresh_from_db()
        self.assertEqual(first.status, PageVariant.Status.RETIRED)
        self.assertEqual(second.status, PageVariant.Status.LIVE)
        self.assertEqual(second.decided_by, self.owner)
        self.client.logout()
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "Second look")
        self.assertContains(response, "palette-plum layout-wide")
        self.assertTrue(AuditEvent.objects.filter(action="storefront.variant_approved", object_id=str(second.pk)).exists())

    def test_reject_and_take_down(self):
        draft = variant(self.product)
        draft.reject(self.owner, "Too busy")
        self.assertEqual(draft.status, PageVariant.Status.REJECTED)
        with self.assertRaises(ValidationError):
            draft.reject(self.owner)
        live = variant(self.product, headline="Live look")
        live.approve(self.owner)
        live.take_down(self.owner)
        self.assertEqual(live.status, PageVariant.Status.RETIRED)
        self.assertNotContains(self.client.get(self.product.get_absolute_url()), "Live look")

    def test_copy_problems_block_approval(self):
        bad = variant(self.product, story="A cup that soothes your sore throat")
        with self.assertRaises(ValidationError):
            bad.approve(self.owner)
        bad.refresh_from_db()
        self.assertEqual(bad.status, PageVariant.Status.DRAFT)

    def test_preview_shows_the_design_and_its_problems(self):
        bad = variant(self.product, palette="buttercup", layout="story", story="Detox in a cup")
        response = self.client.get(bad.get_absolute_url())
        self.assertContains(response, "palette-buttercup layout-story")
        self.assertContains(response, "Fix these before approving")
        self.assertNotContains(response, 'value="approve"')
        self.assertContains(response, '<meta name="robots" content="noindex">')

    def test_decide_view(self):
        draft = variant(self.product, headline="Fresh look")
        url = reverse("storefront:variant_decide", args=[draft.pk])
        response = self.client.post(url, {"decision": "approve", "note": "Lovely"})
        self.assertRedirects(response, reverse("storefront:variant_list"))
        draft.refresh_from_db()
        self.assertEqual((draft.status, draft.decision_note), (PageVariant.Status.LIVE, "Lovely"))
        response = self.client.post(url, {"decision": "reject"})  # a live one can't be rejected
        self.assertRedirects(response, draft.get_absolute_url(), fetch_redirect_response=False)
        draft.refresh_from_db()
        self.assertEqual(draft.status, PageVariant.Status.LIVE)
        self.client.post(url, {"decision": "nonsense"})
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_owner_pages_need_two_factor_owner(self):
        draft = variant(self.product)
        self.client.logout()
        for url in [reverse("storefront:variant_list"), draft.get_absolute_url()]:
            self.assertEqual(self.client.get(url).status_code, 302)
        response = self.client.post(reverse("storefront:variant_decide", args=[draft.pk]), {"decision": "approve"})
        self.assertEqual(response.status_code, 302)
        draft.refresh_from_db()
        self.assertEqual(draft.status, PageVariant.Status.DRAFT)
        customer, device = make_owner(username="customer", staff=False, superuser=False)
        login_verified(self.client, customer, device)
        self.assertEqual(self.client.get(reverse("storefront:variant_list")).status_code, 403)

    def test_variant_list(self):
        variant(self.product, made_by="design-agent")
        response = self.client.get(reverse("storefront:variant_list"))
        self.assertContains(response, "Sencha Morning Mist")
        self.assertContains(response, "Silver Needle")  # the demo's live design

    def test_dashboard_asks_for_approval(self):
        self.assertTrue(any("waiting for your approval" in item.title for item in alerts.attention_items()))
        PageVariant.objects.filter(status=PageVariant.Status.DRAFT).delete()
        self.assertFalse(any("waiting" in item.title for item in alerts.attention_items()))
        self.assertIn(("Page designs to approve", reverse("storefront:variant_list")), attention.shortcuts())

    def test_dashboard_flags_bad_copy_saved_without_checks(self):
        Product.objects.filter(slug="silver-needle").update(summary="Boosts immunity")
        items = [item for item in alerts.attention_items() if item.title.startswith("Product wording")]
        self.assertEqual(len(items), 1)
        self.assertIn("Silver Needle", items[0].detail)


class SubmitVariantCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        demo.load()

    def run_command(self, payload, agent="design-agent"):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as file:
            json.dump(payload, file)
        out = StringIO()
        call_command("submit_page_variant", file.name, agent=agent, stdout=out)
        return out.getvalue()

    def test_saves_drafts_attributed_to_the_agent(self):
        before = PageVariant.objects.count()
        output = self.run_command([
            {"product": "sencha-morning-mist", "palette": "moss", "motif": "fern", "layout": "wide",
             "headline": "Green as spring", "rationale": "Fresh greens"},
            {"product": "dong-ding-oolong", "palette": "bark", "motif": "bee"},
        ])
        self.assertIn("2 design(s) saved", output)
        new = PageVariant.objects.order_by("-pk")[:2]
        self.assertEqual(PageVariant.objects.count(), before + 2)
        self.assertTrue(all(v.status == PageVariant.Status.DRAFT and v.made_by == "design-agent" for v in new))
        event = AuditEvent.objects.filter(action="storefront.variant_proposed").latest("pk")
        self.assertEqual((event.actor_type, event.actor_label), ("agent", "design-agent"))

    def test_rejects_designs_outside_the_theme_or_rules_and_saves_nothing(self):
        before = PageVariant.objects.count()
        for payload, expected in [
            ({"product": "sencha-morning-mist", "palette": "neon", "motif": "leaf"}, "palette"),
            ({"product": "sencha-morning-mist", "palette": "moss", "motif": "dragon"}, "motif"),
            ({"product": "nope", "palette": "moss", "motif": "leaf"}, "No product"),
            ({"product": "sencha-morning-mist", "palette": "moss", "motif": "leaf", "css": "x"}, "Unknown"),
            ({"product": "sencha-morning-mist", "palette": "moss", "motif": "leaf",
              "story": "Boosts your metabolism"}, "health"),
            ([{"product": "sencha-morning-mist", "palette": "moss", "motif": "leaf"}, "oops"], "JSON object"),
        ]:
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(CommandError, expected):
                    self.run_command(payload)
        self.assertEqual(PageVariant.objects.count(), before)

    def test_unreadable_file(self):
        with self.assertRaisesRegex(CommandError, "Cannot read"):
            call_command("submit_page_variant", "/nonexistent/x.json")


class DemoTests(TestCase):
    def test_load_twice_adds_nothing(self):
        demo.load()
        counts = (Product.objects.count(), PageVariant.objects.count())
        demo.load()
        self.assertEqual((Product.objects.count(), PageVariant.objects.count()), counts)

    def test_demo_copy_follows_the_rules(self):
        demo.load()
        for product in Product.objects.all():
            with self.subTest(product=product.slug):
                product.full_clean()
        for page_variant in PageVariant.objects.all():
            page_variant.full_clean()

    @override_settings(PRODUCTION=True)
    def test_refused_in_production(self):
        with self.assertRaisesRegex(CommandError, "never be loaded"):
            call_command("load_demo_catalog")
        self.assertFalse(Product.objects.exists())
