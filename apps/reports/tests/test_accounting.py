"""The daily summary for Wave, against the stand-in client (no call to
Wave's API is made)."""

import json
from datetime import date
from decimal import Decimal
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from apps.reports import accounting
from apps.reports.models import AccountingEntry

from .helpers import at, order, refund

D = Decimal
ACCOUNTS = {key: f"acct-{key}" for key in accounting.ACCOUNT_KEYS}


class Refusing:
    name = "fake"

    def post(self, payload):
        raise accounting.AccountingError("Wave refused it: lineItems.0.accountId: not found")


class SummaryTests(TestCase):
    def setUp(self):
        self.made = order(at(2026, 6, 1, 10), tea="20.00", goods="40.00", shipping="6.00", tax="3.20", fee="2.22")
        order(at(2026, 6, 2, 1), tea="99.00")  # the next day
        refund(order(at(2026, 5, 20), goods="10.00", tax="0.80"), "5.40", at(2026, 6, 1, 15), taxable="5.00",
               tax="0.40")

    def test_figures_of_a_day(self):
        result = accounting.summary(date(2026, 6, 1))
        self.assertEqual((result.orders, result.tea_sales, result.goods_sales, result.shipping),
                         (1, D("20.00"), D("40.00"), D("6.00")))
        self.assertEqual(result.sales_tax, D("2.80"))
        self.assertEqual(result.refunds, D("5.00"))
        self.assertEqual(result.fees, D("2.22"))
        self.assertEqual(result.deposit, D("20") + D("40") + D("6") + D("2.80") - D("5") - D("2.22"))

    @override_settings(WAVE_ACCOUNTS=ACCOUNTS, WAVE_BUSINESS_ID="biz-1", SHOP_NAME="Teashop")
    def test_transaction_for_wave_balances(self):
        payload = accounting.transaction_input(accounting.summary(date(2026, 6, 1)))
        self.assertEqual(payload["externalId"], "teashop-daily-2026-06-01")
        self.assertEqual(payload["anchor"], {"accountId": "acct-anchor", "amount": "61.58", "direction": "DEPOSIT"})
        sides = {line["accountId"]: (line["balance"], line["amount"]) for line in payload["lineItems"]}
        self.assertEqual(sides["acct-refunds"], ("DECREASE", "5.00"))
        self.assertEqual(sides["acct-payment_fees"], ("INCREASE", "2.22"))
        signed = sum(D(amount) * (-1 if account in ("acct-refunds", "acct-payment_fees") else 1)
                     for account, (_side, amount) in sides.items())
        self.assertEqual(signed, D(payload["anchor"]["amount"]))

    def test_posted_once(self):
        entry = accounting.post_day(date(2026, 6, 1))
        self.assertEqual((entry.status, entry.client), (AccountingEntry.Status.POSTED, "fake"))
        self.assertEqual(entry.external_id, "fake-teashop-daily-2026-06-01")
        self.assertEqual(entry.figures["deposit"], "61.58")
        with mock.patch.object(accounting.FakeWave, "post") as post:
            self.assertEqual(accounting.post_day(date(2026, 6, 1)), entry)
        post.assert_not_called()

    def test_a_quiet_day_is_not_posted(self):
        entry = accounting.post_day(date(2026, 1, 1))
        self.assertEqual((entry.status, entry.payload), (AccountingEntry.Status.EMPTY, {}))

    def test_refused_day_is_kept_and_tried_again(self):
        with self.assertRaises(accounting.AccountingError):
            accounting.post_day(date(2026, 6, 1), wave=Refusing())
        entry = AccountingEntry.objects.get(day=date(2026, 6, 1))
        self.assertEqual(entry.status, AccountingEntry.Status.FAILED)
        self.assertIn("not found", entry.error)
        from apps.reports import alerts

        [item] = alerts.attention_items()
        self.assertEqual(item.kind, "jobs")
        self.assertEqual(accounting.post_day(date(2026, 6, 1)).status, AccountingEntry.Status.POSTED)

    def test_days_to_post(self):
        self.assertEqual(accounting.days_to_post(date(2026, 6, 3)), [date(2026, 6, 2)])
        accounting.post_day(date(2026, 5, 30))
        self.assertEqual(accounting.days_to_post(date(2026, 6, 3)), [date(2026, 5, 31), date(2026, 6, 1),
                                                                    date(2026, 6, 2)])
        with override_settings(WAVE_START_DATE="2026-06-01"):
            self.assertEqual(accounting.days_to_post(date(2026, 6, 3)), [date(2026, 6, 1), date(2026, 6, 2)])

    def test_the_job_posts_what_is_waiting(self):
        from apps.reports.jobs import accounting_summary

        with mock.patch.object(accounting, "days_to_post", return_value=[date(2026, 6, 1)]):
            accounting_summary()
        self.assertTrue(AccountingEntry.objects.filter(day=date(2026, 6, 1), status="posted").exists())


class WaveAPITests(TestCase):
    """The real client, against a fake HTTP session: nothing reaches Wave."""

    def session(self, body):
        session = mock.Mock()
        session.post.return_value.json.return_value = body
        session.post.return_value.raise_for_status.return_value = None
        return session

    def test_needs_its_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            accounting.WaveAPI(session=mock.Mock())

    @override_settings(WAVE_TOKEN="token", WAVE_BUSINESS_ID="biz", WAVE_ACCOUNTS=ACCOUNTS)
    def test_posts_the_mutation_and_reads_the_id(self):
        session = self.session({"data": {"moneyTransactionCreate": {"didSucceed": True, "transaction": {"id": "T1"}}}})
        self.assertEqual(accounting.WaveAPI(session=session).post({"externalId": "x"}), "T1")
        sent = json.loads(session.post.call_args.kwargs["data"])
        self.assertIn("moneyTransactionCreate", sent["query"])
        self.assertEqual(sent["variables"], {"input": {"externalId": "x"}})
        self.assertEqual(session.post.call_args.kwargs["headers"]["Authorization"], "Bearer token")

    @override_settings(WAVE_TOKEN="token", WAVE_BUSINESS_ID="biz", WAVE_ACCOUNTS=ACCOUNTS)
    def test_input_errors_are_raised(self):
        session = self.session({"data": {"moneyTransactionCreate": {
            "didSucceed": False, "inputErrors": [{"path": ["input", "anchor"], "message": "bad account"}]}}})
        with self.assertRaisesMessage(accounting.AccountingError, "input.anchor: bad account"):
            accounting.WaveAPI(session=session).post({"externalId": "x"})
