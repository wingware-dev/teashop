"""Sales per state against nexus thresholds, the dashboard's checkout
items, the policy pages and the Content-Security-Policy header."""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.test import override_settings
from django.utils import timezone

from apps.checkout import alerts, nexus, tax
from apps.checkout.models import ZERO, CheckoutSettings, NexusThreshold, Order, OrderLine
from apps.core.testing import login_verified, make_owner
from apps.fulfillment.models import Refund

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


def local(*args):
    return datetime(*args, 12, tzinfo=timezone.get_current_timezone())


def refund(order, amount, when, kind="partial", **what):
    """A Refund recording the tax refund_tax gives back, as the fulfillment
    service does (without its payment provider)."""
    earlier = order.refunds.aggregate(amount=Sum("amount"), taxable=Sum("taxable_amount"), tax=Sum("tax_amount"))
    taxable, tax_amount = tax.refund_tax(order, Decimal(amount), before=tuple(
        earlier[key] or ZERO for key in ("amount", "taxable", "tax")), **what)
    return Refund.objects.create(order=order, kind=kind, amount=Decimal(amount), taxable_amount=taxable,
                                 tax_amount=tax_amount, reason="test", created_at=when)


def ny_order(when, total="108.00", taxable="40.00", tax="8.00", **fields):
    """$100 of goods ($40 of it taxable) plus $8 tax."""
    fields.setdefault("status", Order.Status.PAID)
    return Order.objects.create(email="a@example.com", ship_state="NY", total=Decimal(total),
                                taxable_amount=Decimal(taxable), tax_amount=Decimal(tax), paid_at=when, **fields)


class RefundNettingTests(CheckoutTestCase):
    """Refunds come off the tax and nexus figures in the period they were
    issued in, taking their share of the tax with them."""

    def quarters(self, today=date(2025, 12, 31)):
        return dict(nexus.ny_tax_by_quarter(2025, today))

    def test_full_refund_in_a_later_quarter_comes_off_that_quarter(self):
        order = ny_order(local(2025, 2, 10))
        refund(order, "108.00", local(2025, 5, 3), kind="full")
        q1, q2 = self.quarters()["2025 Q1"], self.quarters()["2025 Q2"]
        self.assertEqual((q1["orders"], q1["sales"], q1["taxable"], q1["tax"], q1["refunds"]),
                         (1, Decimal("108.00"), Decimal("40.00"), Decimal("8.00"), 0))
        self.assertEqual((q2["orders"], q2["sales"], q2["taxable"], q2["tax"]),
                         (0, Decimal("-108.00"), Decimal("-40.00"), Decimal("-8.00")))
        self.assertEqual((q2["refunds"], q2["refunded"]), (1, Decimal("108.00")))

    def test_partial_refund_takes_its_share_of_the_tax(self):
        order = ny_order(local(2025, 2, 10))
        refund(order, "27.00", local(2025, 2, 20))  # a quarter of the total
        q1 = self.quarters()["2025 Q1"]
        self.assertEqual((q1["sales"], q1["taxable"], q1["tax"]), (Decimal("81.00"), Decimal("30.00"), Decimal("6.00")))

    def test_partial_refunds_add_up_to_exactly_the_tax_collected(self):
        order = ny_order(local(2025, 2, 10), total="10.00", taxable="10.00", tax="0.80")
        for day, amount in ((11, "3.33"), (12, "3.33"), (13, "3.34")):
            refund(order, amount, local(2025, 2, day))
        shares = nexus.refund_shares(order=order)
        self.assertEqual([s.tax for s in shares], [Decimal("0.27"), Decimal("0.26"), Decimal("0.27")])
        self.assertEqual(sum(s.tax for s in shares), Decimal("0.80"))
        self.assertEqual(sum(s.taxable for s in shares), Decimal("10.00"))
        q1 = self.quarters()["2025 Q1"]
        self.assertEqual((q1["sales"], q1["taxable"], q1["tax"]), (ZERO, ZERO, ZERO))

    def test_refund_of_an_overpayment_is_not_a_sale(self):
        order = ny_order(local(2025, 2, 10), amount_received=Decimal("120.00"))
        refund(order, "120.00", local(2025, 2, 11), kind="full")
        q1 = self.quarters()["2025 Q1"]
        self.assertEqual((q1["sales"], q1["tax"]), (ZERO, ZERO))

    def test_cancelled_order_counts_where_paid_and_its_refund_where_issued(self):
        order = ny_order(local(2025, 3, 30), status=Order.Status.CANCELLED)
        refund(order, "108.00", local(2025, 4, 2), kind="cancellation")
        ny_order(None, status=Order.Status.CANCELLED)  # never paid: never counted
        quarters = self.quarters()
        self.assertEqual((quarters["2025 Q1"]["sales"], quarters["2025 Q1"]["tax"]), (Decimal("108.00"), Decimal("8.00")))
        self.assertEqual((quarters["2025 Q2"]["sales"], quarters["2025 Q2"]["tax"]), (Decimal("-108.00"), Decimal("-8.00")))

    def test_other_states_refunds_stay_out_of_new_york(self):
        nj = Order.objects.create(email="a@example.com", ship_state="NJ", status=Order.Status.PAID,
                                  total=Decimal("50.00"), paid_at=local(2025, 2, 10))
        refund(nj, "50.00", local(2025, 2, 11), kind="full")
        q1 = self.quarters()["2025 Q1"]
        self.assertEqual((q1["orders"], q1["sales"], q1["refunds"]), (0, ZERO, 0))

    def test_nexus_sales_net_of_refunds_without_their_tax(self):
        order = ny_order(local(2024, 12, 20))
        refund(order, "54.00", local(2025, 1, 5))  # half: $50 of sales, $4 of tax
        nj = Order.objects.create(email="a@example.com", ship_state="NJ", status=Order.Status.CANCELLED,
                                  total=Decimal("60.00"), paid_at=local(2025, 3, 1))
        refund(nj, "60.00", local(2025, 3, 2), kind="cancellation")
        self.assertEqual(nexus.sales_by_state(2024), {"NY": (Decimal("100.00"), 1)})
        this_year = nexus.sales_by_state(2025)
        self.assertEqual(this_year["NY"], (Decimal("-50.00"), 0))
        self.assertEqual(this_year["NJ"], (ZERO, 0))

    def test_report_page_shows_refunds_and_explains_the_period(self):
        today = timezone.localdate()
        order = ny_order(timezone.now() - timedelta(minutes=5))
        refund(order, "27.00", timezone.now())
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        page = self.client.get("/owner/checkout/sales-by-state/")
        self.assertContains(page, "$27.00 (1)")
        self.assertContains(page, "comes off the quarter it was issued in")
        self.assertEqual(dict(nexus.ny_tax_by_quarter(today.year, today))[
            f"{today.year} Q{(today.month - 1) // 3 + 1}"]["tax"], Decimal("6.00"))


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
