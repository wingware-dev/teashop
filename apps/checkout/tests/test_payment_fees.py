"""Stripe's fee on each payment, kept on the order for the profit reports."""

from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from apps import jobs
from apps.checkout import payments
from apps.checkout.jobs import record_payment_fee
from apps.checkout.models import Order


def stripe_order(**fields):
    return Order.objects.create(email="a@example.com", status=Order.Status.PAID, total=Decimal("36.00"),
                                paid_at=timezone.now(), payment_provider="stripe", payment_id="pi_123", **fields)


class Dictish(SimpleNamespace):
    def to_dict(self):
        return self.data


def client_returning(intent):
    client = mock.Mock()
    client.v1.payment_intents.retrieve.return_value = Dictish(data=intent)
    return client


class StripeFeeTests(TestCase):
    def test_reads_the_fee_from_the_balance_transaction(self):
        client = client_returning({"latest_charge": {"balance_transaction": {"fee": 134}}})
        self.assertEqual(payments.StripePayments(client).payment_fee(stripe_order()), Decimal("1.34"))
        args = client.v1.payment_intents.retrieve.call_args
        self.assertEqual(args.args[0], "pi_123")
        self.assertEqual(args.kwargs["params"], {"expand": ["latest_charge.balance_transaction"]})

    def test_not_settled_yet(self):
        client = client_returning({"latest_charge": {"balance_transaction": None}})
        self.assertIsNone(payments.StripePayments(client).payment_fee(stripe_order()))

    def test_the_stand_in_knows_no_fee(self):
        self.assertIsNone(payments.FakePayments().payment_fee(stripe_order()))


@override_settings(PAYMENT_PROVIDER="stripe", STRIPE_SECRET_KEY="sk_test_x")
class FeeJobTests(TestCase):
    def test_keeps_the_fee(self):
        order = stripe_order()
        with mock.patch.object(payments.StripePayments, "__init__", return_value=None), \
                mock.patch.object(payments.StripePayments, "payment_fee", return_value=Decimal("1.34")):
            record_payment_fee(order.pk)
        order.refresh_from_db()
        self.assertEqual(order.payment_fee, Decimal("1.34"))

    def test_asks_again_later_until_stripe_settles_it(self):
        order = stripe_order()
        with mock.patch.object(payments.StripePayments, "__init__", return_value=None), \
                mock.patch.object(payments.StripePayments, "payment_fee", return_value=None):
            with self.assertRaises(jobs.Retry):
                record_payment_fee(order.pk)

    def test_other_orders_are_left_alone(self):
        with mock.patch.object(payments.StripePayments, "payment_fee") as fee:
            record_payment_fee(stripe_order(payment_fee=Decimal("1.00")).pk)
            record_payment_fee(999999)
        fee.assert_not_called()

    @override_settings(JOBS_EAGER=False)
    def test_paid_orders_queue_it(self):
        from apps.checkout.orders import queue_payment_fee
        from apps.jobs.models import Job

        queue_payment_fee(stripe_order())
        queue_payment_fee(Order.objects.create(email="b@example.com", payment_provider="fake"))
        self.assertEqual(Job.objects.filter(name="apps.checkout.jobs.record_payment_fee").count(), 1)
