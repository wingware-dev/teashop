"""Sales per state against nexus thresholds, the dashboard's checkout
items, the policy pages and the Content-Security-Policy header."""

from datetime import timedelta
from decimal import Decimal

from django.test import override_settings
from django.utils import timezone

from apps.checkout import alerts, nexus
from apps.checkout.models import CheckoutSettings, NexusThreshold, Order
from apps.core.testing import login_verified, make_owner

from .helpers import CheckoutTestCase


def paid(state, total, tax="0", days_ago=1, **fields):
    return Order.objects.create(email="a@example.com", status=Order.Status.PAID, ship_state=state,
                                total=Decimal(total), tax_amount=Decimal(tax),
                                paid_at=timezone.now() - timedelta(days=days_ago), **fields)


class NexusTests(CheckoutTestCase):
    def test_thresholds_seeded(self):
        self.assertEqual(NexusThreshold.objects.get(state="NY").sales, Decimal("500000"))
        self.assertFalse(NexusThreshold.objects.get(state="OR").has_sales_tax)
        self.assertEqual(NexusThreshold.objects.count(), 49)

    def test_sales_exclude_tax_and_compare_with_the_threshold(self):
        paid("NJ", "85010", tax="10")
        row = next(r for r in nexus.report() if r.state == "NJ")
        self.assertEqual(row.sales, Decimal("85000"))
        self.assertEqual(row.percent, 85)
        self.assertTrue(row.needs_action)
        self.assertIn("Nearing", row.status)

    def test_transactions_count_where_either_measure_applies(self):
        for _ in range(170):
            paid("OH", "10")
        row = next(r for r in nexus.report() if r.state == "OH")
        self.assertEqual(row.percent, 85)

    def test_both_measures_needed_in_new_york_but_it_collects_anyway(self):
        row = next(r for r in nexus.report() if r.state == "NY")
        self.assertTrue(row.collecting)
        self.assertFalse(row.needs_action)
        threshold = NexusThreshold.objects.get(state="NY")
        self.assertEqual(nexus.share_of(threshold, Decimal("600000"), 50), 0.5)

    def test_dashboard_warns_and_the_report_page_shows_it(self):
        paid("NJ", "120000")
        titles = [item.title for item in alerts.attention_items()]
        self.assertTrue(any("New Jersey" in t for t in titles))
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        page = self.client.get("/owner/checkout/sales-by-state/")
        self.assertContains(page, "Threshold passed")


class AttentionTests(CheckoutTestCase):
    def test_late_orders_are_urgent(self):
        paid("NY", "20", ship_by=timezone.localdate() - timedelta(days=1), confirmation_sent_at=timezone.now())
        item = next(i for i in alerts.attention_items() if "promised ship date" in i.title)
        self.assertEqual(item.level, "urgent")

    def test_unsent_confirmation_and_fallback_tax(self):
        paid("NY", "20", days_ago=1, tax_fallback=True, ship_zip="14850")
        titles = " | ".join(i.title for i in alerts.attention_items())
        self.assertIn("confirmations not sent", titles)
        self.assertIn("Sales tax rates missing", titles)

    def test_vacation_reminder(self):
        CheckoutSettings.objects.update_or_create(pk=1, defaults={"vacation_mode": True,
                                                                  "vacation_message": "Away"})
        self.assertTrue(any(i.title == "Vacation mode is on" for i in alerts.attention_items()))


class PolicyTests(CheckoutTestCase):
    def test_every_policy_answers_even_while_closed(self):
        with override_settings(STOREFRONT_OPEN=False):
            for slug in ("privacy", "terms", "returns", "shipping", "subscriptions", "accessibility"):
                with self.subTest(slug=slug):
                    self.assertEqual(self.client.get(f"/policies/{slug}/").status_code, 200)
        self.assertEqual(self.client.get("/policies/nonsense/").status_code, 404)

    def test_privacy_names_every_service_including_the_ai_provider(self):
        page = self.client.get("/policies/privacy/")
        for name in ("Stripe", "EasyPost", "Postal Service", "Anthropic", "Cloudflare", "Backblaze", "Sentry",
                     "email service", "hosting provider"):
            self.assertContains(page, name)

    def test_shipping_policy_states_the_threshold_when_set(self):
        self.assertNotContains(self.client.get("/policies/shipping/"), "ship free")
        CheckoutSettings.objects.update_or_create(pk=1, defaults={"free_shipping_over": Decimal("40")})
        self.assertContains(self.client.get("/policies/shipping/"), "$40.00 or more")

    def test_footer_links_the_policies(self):
        self.assertContains(self.client.get("/"), "/policies/privacy/")

    def test_robots_keeps_checkout_pages_out(self):
        body = self.client.get("/robots.txt").content.decode()
        for path in ("/cart/", "/checkout/", "/orders/", "/your-account/"):
            self.assertIn(f"Disallow: {path}", body)


class SecurityHeaderTests(CheckoutTestCase):
    def test_csp_allows_only_our_assets_and_stripe(self):
        policy = self.client.get("/").headers["Content-Security-Policy"]
        directives = dict(part.strip().split(" ", 1) for part in policy.split(";") if part.strip())
        self.assertEqual(directives["default-src"], "'self'")
        self.assertIn("https://js.stripe.com", directives["script-src"])
        self.assertNotIn("unsafe-inline", directives["script-src"])
        self.assertNotIn("unsafe-inline", directives["style-src"])
        self.assertIn("https://hooks.stripe.com", directives["frame-src"])
        self.assertIn("https://api.stripe.com", directives["connect-src"])
        self.assertEqual(directives["frame-ancestors"], "'none'")
