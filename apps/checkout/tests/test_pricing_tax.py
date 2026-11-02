"""Figures: discounts, free shipping, and New York sales tax with the
shipping split between tea (exempt) and merchandise (taxable)."""

from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import override_settings
from django.utils import timezone

from apps.catalog.models import Product
from apps.checkout import tax
from apps.checkout.models import CheckoutSettings, DiscountCode, Order, TaxRate
from apps.checkout.pricing import allocate, quote
from apps.checkout.shipping import Address, Rate

from .helpers import CheckoutTestCase, fake_size

D = Decimal
ALBANY = Address(name="A", street1="1 Main St", city="Albany", state="NY", zip="12207")
GROUND = Rate(id="r1", service="GroundAdvantage", amount=D("6.00"))
PRIORITY = Rate(id="r2", service="Priority", amount=D("10.00"))


class TaxSplitTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        TaxRate.objects.create(state="NY", zip_prefix="122", rate=D("0.08"), jurisdiction="Albany County")

    def test_tea_only_order_has_no_tax_even_on_shipping(self):
        result = tax.calculate([(D("30.00"), False)], D("6.00"), ALBANY)
        self.assertEqual((result.tax, result.taxable_amount), (D("0.00"), D("0.00")))

    def test_merch_only_taxes_items_and_all_shipping(self):
        result = tax.calculate([(D("40.00"), True)], D("10.00"), ALBANY)
        self.assertEqual(result.taxable_amount, D("50.00"))
        self.assertEqual(result.tax, D("4.00"))

    def test_mixed_order_taxes_only_the_merch_share_of_shipping(self):
        # $30 tea + $10 mug: the mug is a quarter of the items, so a quarter
        # of the $8 shipping ($2) is taxable with it.
        result = tax.calculate([(D("30.00"), False), (D("10.00"), True)], D("8.00"), ALBANY)
        self.assertEqual(result.taxable_amount, D("12.00"))
        self.assertEqual(result.tax, D("0.96"))
        self.assertEqual(result.jurisdiction, "Albany County")

    def test_no_tax_outside_states_where_the_shop_collects(self):
        result = tax.calculate([(D("40.00"), True)], D("10.00"), Address(state="CA", zip="94110"))
        self.assertEqual(result.tax, D("0.00"))
        self.assertIn("California", result.jurisdiction)

    def test_longest_zip_match_wins(self):
        TaxRate.objects.create(state="NY", zip_prefix="12207", rate=D("0.085"), jurisdiction="Special")
        TaxRate.objects.create(state="NY", zip_prefix="", rate=D("0.04"), jurisdiction="State only")
        self.assertEqual(TaxRate.lookup("NY", "12207-1234").jurisdiction, "Special")
        self.assertEqual(TaxRate.lookup("NY", "12208").jurisdiction, "Albany County")
        self.assertEqual(TaxRate.lookup("NY", "14850").jurisdiction, "State only")

    def test_missing_zip_rate_charges_the_fallback_and_flags_it(self):
        result = tax.calculate([(D("10.00"), True)], D("0"), Address(state="NY", zip="14850"))
        self.assertTrue(result.fallback)
        self.assertEqual(result.rate, D("0.08875"))
        self.assertEqual(result.tax, D("0.89"))

    def test_rounding_is_half_up_to_the_cent(self):
        TaxRate.objects.create(state="NY", zip_prefix="10001", rate=D("0.08875"), jurisdiction="NYC")
        result = tax.calculate([(D("10.00"), True)], D("0"), Address(state="NY", zip="10001"))
        self.assertEqual(result.tax, D("0.89"))  # 0.8875 -> 0.89

    @override_settings(TAX_PROVIDER="stripe")
    def test_stripe_tax_gets_only_the_taxable_base(self):
        calculation = mock.Mock(id="taxcalc_1", tax_amount_exclusive=96)
        client = mock.Mock()
        client.v1.tax.calculations.create.return_value = calculation
        with mock.patch("apps.checkout.payments.stripe_client", return_value=client):
            result = tax.calculate([(D("30.00"), False), (D("10.00"), True)], D("8.00"), ALBANY)
        params = client.v1.tax.calculations.create.call_args.kwargs["params"]
        self.assertEqual(params["line_items"][0]["amount"], 1200)
        self.assertEqual(params["customer_details"]["address"]["postal_code"], "12207")
        self.assertEqual((result.tax, result.calculation_id), (D("0.96"), "taxcalc_1"))


class AllocateTests(CheckoutTestCase):
    def test_parts_add_up_exactly(self):
        parts = allocate(D("10.00"), [D("3.33"), D("3.33"), D("3.34")])
        self.assertEqual(sum(parts), D("10.00"))

    def test_nothing_to_split(self):
        self.assertEqual(allocate(D("0"), [D("1"), D("2")]), [D("0.00"), D("0.00")])
        self.assertEqual(allocate(D("5"), [D("0"), D("0")]), [D("0.00"), D("0.00")])


class QuoteTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        TaxRate.objects.create(state="NY", zip_prefix="", rate=D("0.08"), jurisdiction="NY")
        self.tea = fake_size("30.00")
        self.mug = fake_size("10.00", Product.Kind.GOODS)
        self.shop = CheckoutSettings(free_shipping_over=None)

    def test_percent_discount_is_shared_over_lines_and_lowers_the_tax_base(self):
        code = DiscountCode.objects.create(code="TEN", kind=DiscountCode.Kind.PERCENT, value=D("10"))
        result = quote([(self.tea, 1), (self.mug, 1)], discount=code, rates=[GROUND], rate=GROUND, address=ALBANY,
                       settings=self.shop)
        self.assertEqual(result.discount_amount, D("4.00"))
        self.assertEqual([line.discount_share for line in result.lines], [D("3.00"), D("1.00")])
        # Mug $9 of $36 items: a quarter of $6 shipping is taxable.
        self.assertEqual(result.tax.taxable_amount, D("10.50"))
        self.assertEqual(result.total, D("36.00") + D("6.00") + D("0.84"))

    def test_amount_discount_never_exceeds_the_items(self):
        code = DiscountCode.objects.create(code="BIG", kind=DiscountCode.Kind.AMOUNT, value=D("50"))
        result = quote([(self.mug, 1)], discount=code, settings=self.shop)
        self.assertEqual(result.discount_amount, D("10.00"))
        self.assertEqual(result.items_total, D("0.00"))

    def test_code_below_its_minimum_is_dropped_with_a_reason(self):
        code = DiscountCode.objects.create(code="MIN", kind=DiscountCode.Kind.AMOUNT, value=D("5"),
                                           min_subtotal=D("50"))
        result = quote([(self.tea, 1)], discount=code, settings=self.shop)
        self.assertIsNone(result.discount)
        self.assertIn("at least $50.00", result.discount_problem)

    def test_expired_and_used_up_codes(self):
        today = timezone.localdate()
        expired = DiscountCode.objects.create(code="OLD", kind=DiscountCode.Kind.AMOUNT, value=D("5"),
                                              ends_on=today - timedelta(days=1))
        self.assertIn("not valid", expired.problem(D("100")))
        used = DiscountCode.objects.create(code="ONCE", kind=DiscountCode.Kind.AMOUNT, value=D("5"), max_uses=1)
        Order.objects.create(email="a@example.com", status=Order.Status.PAID, discount=used)
        self.assertIn("used up", used.problem(D("100")))

    def test_once_per_customer(self):
        code = DiscountCode.objects.create(code="HELLO", kind=DiscountCode.Kind.AMOUNT, value=D("5"),
                                           once_per_customer=True)
        Order.objects.create(email="ada@example.com", status=Order.Status.PAID, discount=code)
        self.assertIsNotNone(code.problem(D("100"), "ADA@example.com"))
        self.assertIsNone(code.problem(D("100"), "bob@example.com"))

    def test_free_shipping_threshold_makes_only_the_cheapest_service_free(self):
        shop = CheckoutSettings(free_shipping_over=D("35.00"))
        ground = quote([(self.tea, 1), (self.mug, 1)], rates=[GROUND, PRIORITY], rate=GROUND, settings=shop)
        priority = quote([(self.tea, 1), (self.mug, 1)], rates=[GROUND, PRIORITY], rate=PRIORITY, settings=shop)
        self.assertEqual(ground.shipping_amount, D("0"))
        self.assertEqual(priority.shipping_amount, D("10.00"))

    def test_free_shipping_gap_is_measured_after_discounts(self):
        shop = CheckoutSettings(free_shipping_over=D("35.00"))
        result = quote([(self.tea, 1)], settings=shop)
        self.assertEqual(result.free_shipping_gap, D("5.00"))
        self.assertFalse(result.free_shipping)

    def test_free_shipping_code(self):
        code = DiscountCode.objects.create(code="SHIPFREE", kind=DiscountCode.Kind.FREE_SHIPPING)
        result = quote([(self.mug, 1)], discount=code, rates=[GROUND], rate=GROUND, address=ALBANY,
                       settings=self.shop)
        self.assertTrue(result.free_shipping)
        self.assertEqual(result.shipping_amount, D("0"))
        self.assertEqual(result.tax.taxable_amount, D("10.00"))

    def test_prices_ignore_who_is_buying(self):
        a = quote([(self.tea, 2)], email="one@example.com", settings=self.shop)
        b = quote([(self.tea, 2)], email="two@example.com", settings=self.shop)
        self.assertEqual(a.total, b.total)
