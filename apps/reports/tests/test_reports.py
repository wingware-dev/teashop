"""Sales, margin and tax figures."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, override_settings

from apps.checkout.models import Order, Subscription, SubscriptionPlan
from apps.purchasing import reports as purchasing
from apps.reports import sales, taxes

from .helpers import at, order, refund

D = Decimal


class SalesTests(TestCase):
    def setUp(self):
        self.a = order(at(2026, 3, 3), tea="20.00", goods="40.00", discount="5.00", shipping="6.00", tax="3.20")
        self.b = order(at(2026, 3, 20), tea="15.00", shipping="5.00")
        self.c = order(at(2026, 4, 2), goods="30.00", shipping="4.00", tax="2.40")
        order(at(2026, 4, 3), tea="99.00", status=Order.Status.PENDING)  # never paid
        refund(self.a, "10.00", at(2026, 4, 5))

    def test_by_month_counts_refunds_when_given(self):
        rows, total = sales.by_period(date(2026, 3, 1), date(2026, 5, 1), "month")
        march, april = rows
        self.assertEqual((march.label, march.orders, march.gross, march.discounts), ("March 2026", 2, D("75.00"), D("5.00")))
        self.assertEqual(march.net, D("70.00") + D("11.00"))
        self.assertEqual(march.tax, D("3.20"))
        self.assertEqual(april.refunds, D("10.00"))
        self.assertEqual(april.net, D("34.00") - D("10.00"))
        self.assertEqual(total.net, march.net + april.net)
        self.assertEqual(total.orders, 3)

    def test_periods_cover_the_range_even_when_empty(self):
        rows, _total = sales.by_period(date(2026, 3, 1), date(2026, 3, 15), "week")
        self.assertEqual(rows[0].start, date(2026, 2, 23))  # the Monday
        self.assertEqual(len(rows), 3)
        self.assertEqual(sales.period_label(date(2026, 4, 1), "quarter"), "2026 Q2")

    def test_by_product_category_and_channel(self):
        plan = SubscriptionPlan.objects.create(name="Tea of the month", slug="totm", description="Two teas",
                                               price=D("24"))
        sub = Subscription.objects.create(plan=plan, email="s@example.com", price=D("24"), interval_months=1,
                                          terms_text="t", consented_at=at(2026, 3, 1))
        order(at(2026, 3, 10), tea="24.00", subscription=sub)
        products = {r.label: r for r in sales.by_product(date(2026, 3, 1), date(2026, 4, 1))}
        self.assertEqual(products["Teapot"].items, D("40.00"))
        # 20 less the discount, 15, and the subscription delivery's 24.
        self.assertEqual(products["Assam"].items, D("54.00"))
        channels = {r.label: r for r in sales.by_channel(date(2026, 3, 1), date(2026, 5, 1))}
        self.assertEqual(channels["Subscriptions"].net, D("24.00"))
        self.assertEqual(channels["Shop"].refunds, D("10.00"))
        categories = {r.label for r in sales.by_category(date(2026, 3, 1), date(2026, 4, 1))}
        self.assertEqual(categories, {"Teas, no category", "Merchandise, no category"})


class OrderProfitTests(TestCase):
    def test_margin_after_shipping_postage_and_fees(self):
        from apps.fulfillment.models import Parcel, PostageLabel

        known = order(at(2026, 5, 1), tea="30.00", shipping="6.00", fee="1.34")
        Parcel.objects.create(order=known)
        PostageLabel.objects.create(parcel=known.parcels.get(), provider="fake", service="GroundAdvantage",
                                    tracking_number="1", postage=D("5.10"), weight_grams=200)
        PostageLabel.objects.create(parcel=known.parcels.get(), provider="fake", service="GroundAdvantage",
                                    tracking_number="2", postage=D("9.00"), weight_grams=200,
                                    voided_at=at(2026, 5, 1))
        guessed = order(at(2026, 5, 2), tea="10.00", provider="fake")
        rows = {row.order.pk: row for row in purchasing.order_profit(date(2026, 5, 1), date(2026, 6, 1))}
        row = rows[known.pk]
        self.assertEqual((row.revenue, row.postage, row.fee, row.fee_estimated), (D("36.00"), D("5.10"), D("1.34"), False))
        self.assertEqual(row.margin, D("36.00") - D("5.10") - D("1.34"))
        estimate = rows[guessed.pk]
        self.assertTrue(estimate.fee_estimated)
        self.assertEqual(estimate.fee, D("0.59"))  # 2.9% of $10 + 30¢
        total = purchasing.order_totals(rows.values())
        self.assertEqual(total.revenue, D("46.00"))
        self.assertTrue(total.fee_estimated)

    @override_settings(PRODUCTION=True)
    def test_test_labels_cost_nothing_on_the_server(self):
        from apps.fulfillment.models import Parcel, PostageLabel

        made = order(at(2026, 5, 1), tea="30.00")
        parcel = Parcel.objects.create(order=made)
        PostageLabel.objects.create(parcel=parcel, provider="easypost", service="x", tracking_number="1",
                                    postage=D("5.10"), weight_grams=200, test_mode=True)
        self.assertEqual(purchasing.postage_paid([made]), {})

    def test_margin_summary(self):
        order(at(2026, 5, 1), tea="30.00", shipping="6.00", fee="1.00")
        m = sales.margin(date(2026, 5, 1), date(2026, 6, 1))
        self.assertEqual(m.net_sales, D("36.00"))
        self.assertEqual(m.goods_cost, D("0.00"))
        self.assertEqual(m.after_fulfilment, D("35.00"))


class SalesTaxTests(TestCase):
    def test_new_york_quarters(self):
        self.assertEqual(taxes.ny_quarter(date(2026, 1, 15)).start, date(2025, 12, 1))
        q = taxes.ny_quarter(date(2026, 4, 30))
        self.assertEqual((q.start, q.end, q.due), (date(2026, 3, 1), date(2026, 6, 1), date(2026, 6, 20)))
        self.assertEqual(q.label, "Mar 2026 to May 2026")
        self.assertEqual(taxes.ny_quarter(date(2026, 11, 30)).start, date(2026, 9, 1))
        quarters = taxes.ny_quarters(date(2026, 4, 1), count=3)
        self.assertEqual([p.start for p in quarters], [date(2026, 3, 1), date(2025, 12, 1), date(2025, 9, 1)])

    def test_return_by_jurisdiction_less_refunds_in_the_quarter(self):
        albany = order(at(2026, 3, 5), tea="20.00", goods="40.00", tax="3.20", jurisdiction="Albany County",
                       rate="0.08")
        order(at(2026, 4, 5), goods="10.00", tax="0.89", jurisdiction="New York City", rate="0.08875")
        order(at(2026, 4, 6), goods="50.00", state="NJ")
        order(at(2026, 2, 27), goods="10.00", tax="0.80", jurisdiction="Albany County", rate="0.08")  # last quarter
        refund(albany, "10.80", at(2026, 5, 1), taxable="10.00", tax="0.80")
        result = taxes.ny_sales_tax(taxes.ny_quarter(date(2026, 3, 1)))
        self.assertEqual(result.orders, 2)
        self.assertEqual(result.gross, D("70.00") - D("10.00"))
        self.assertEqual(result.taxable, D("40.00"))
        self.assertEqual(result.nontaxable, D("20.00"))
        self.assertEqual(result.tax, D("3.29"))
        self.assertEqual(result.outside, D("50.00"))
        places = {j.name: j for j in result.jurisdictions}
        self.assertEqual(places["Albany County"].tax, D("2.40"))
        self.assertEqual(places["Albany County"].rate_percent, D("8"))
        self.assertEqual(places["New York City"].rate_percent, D("8.875"))


class EstimatedTaxTests(TestCase):
    def test_self_employment_tax(self):
        self.assertEqual(taxes.self_employment_tax(D("10000")), D("1412.96"))
        self.assertEqual(taxes.self_employment_tax(D("-50")), D("0.00"))
        with override_settings(SOCIAL_SECURITY_WAGE_BASE=D("1000")):
            self.assertEqual(taxes.self_employment_tax(D("10000")), D("124.00") + D("267.82"))

    @override_settings(ESTIMATED_TAX_FEDERAL_RATE=D("0.10"), ESTIMATED_TAX_STATE_RATE=D("0.05"))
    def test_payments_by_period(self):
        order(at(2026, 2, 1), tea="1000.00", fee="0")
        order(at(2026, 5, 1), tea="500.00", fee="0")
        rows = taxes.estimated_tax(2026, today=date(2026, 7, 1))
        first, second, third, fourth = rows
        self.assertEqual(first.profit, D("1000.00"))
        self.assertEqual(first.se_tax, D("141.30"))
        self.assertEqual(first.federal, D("92.94"))  # (1000 - 70.65) x 10%
        self.assertEqual(first.payment, first.total_to_date)
        self.assertEqual(second.to_date, D("1500.00"))
        self.assertEqual(second.payment, second.total_to_date - first.total_to_date)
        self.assertTrue(third.started)
        self.assertEqual(third.payment, D("0.00"))
        self.assertFalse(fourth.started)
        self.assertEqual(fourth.period.due, date(2027, 1, 15))
