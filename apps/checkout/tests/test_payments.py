"""Stripe: what the shop asks of it (with the client stood in), the
webhook's signature check, and what each event does."""

import hashlib
import hmac
import json
import time
from decimal import Decimal
from unittest import mock

from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from apps.checkout import payments, webhooks
from apps.checkout.models import Order, WebhookEvent
from apps.checkout.payments import StripePayments

from .helpers import CheckoutTestCase, checkout_to_payment, load_catalog

SECRET = "whsec_test_secret"


def signed(payload):
    stamp = int(time.time())
    signature = hmac.new(SECRET.encode(), f"{stamp}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"t={stamp},v1={signature}"


def event(kind, obj, event_id="evt_1"):
    return {"id": event_id, "object": "event", "type": kind, "data": {"object": obj}}


class ProviderChoiceTests(SimpleTestCase):
    @override_settings(PAYMENT_PROVIDER="fake", PRODUCTION=True)
    def test_stand_in_refused_in_production(self):
        with self.assertRaises(ImproperlyConfigured):
            payments.provider()
        self.assertFalse(payments.is_configured())

    @override_settings(PAYMENT_PROVIDER="stripe", STRIPE_SECRET_KEY="sk_test_x", STRIPE_PUBLISHABLE_KEY="pk_test_x",
                       STRIPE_WEBHOOK_SECRET="")
    def test_stripe_needs_the_webhook_secret(self):
        self.assertFalse(payments.is_configured())

    def test_live_keys_refused_without_approval(self):
        import os
        import subprocess
        import sys

        from django.conf import settings

        env = {**os.environ, "STRIPE_SECRET_KEY": "sk_live_abc", "STRIPE_ALLOW_LIVE": "", "DJANGO_ENV": "dev"}
        result = subprocess.run([sys.executable, "-c", "import config.settings"], env=env, capture_output=True,
                                text=True, cwd=settings.BASE_DIR, timeout=60)
        self.assertIn("STRIPE_ALLOW_LIVE", result.stderr)


@override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_PUBLISHABLE_KEY="pk_test_x")
class StripeRequestTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        tea, _ = load_catalog()
        checkout_to_payment(self.client, tea)
        self.order = Order.objects.get()
        self.client_mock = mock.Mock()

    def test_new_payment_intent_for_the_order_total(self):
        self.client_mock.v1.payment_intents.create.return_value = mock.Mock(id="pi_1", client_secret="pi_1_secret")
        started = StripePayments(self.client_mock).start_payment(self.order)
        params = self.client_mock.v1.payment_intents.create.call_args.kwargs["params"]
        self.assertEqual(params["amount"], self.order.total_cents)
        self.assertEqual(params["currency"], "usd")
        self.assertEqual(params["automatic_payment_methods"], {"enabled": True})
        self.assertEqual(params["metadata"], {"order_number": self.order.number})
        self.assertEqual(params["shipping"]["address"]["postal_code"], "12207")
        self.assertEqual((started.id, started.client_secret), ("pi_1", "pi_1_secret"))
        # Nothing that could hold card data is sent or kept by the shop.
        self.assertNotIn("payment_method_data", params)

    def test_existing_payment_intent_is_updated_not_duplicated(self):
        self.order.payment_id = "pi_1"
        self.client_mock.v1.payment_intents.update.return_value = mock.Mock(id="pi_1", client_secret="s")
        StripePayments(self.client_mock).start_payment(self.order)
        self.client_mock.v1.payment_intents.create.assert_not_called()
        self.assertEqual(self.client_mock.v1.payment_intents.update.call_args.args[0], "pi_1")

    def test_stripe_failure_becomes_a_customer_message(self):
        import stripe

        self.client_mock.v1.payment_intents.create.side_effect = stripe.APIConnectionError("down")
        with self.assertRaises(payments.PaymentError):
            StripePayments(self.client_mock).start_payment(self.order)


@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
class WebhookTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        tea, _ = load_catalog()
        checkout_to_payment(self.client, tea)
        self.order = Order.objects.get()
        self.order.payment_id = "pi_123"
        self.order.save()

    def post(self, body, signature=None):
        payload = json.dumps(body)
        return self.client.post("/checkout/stripe-webhook/", payload, content_type="application/json",
                                HTTP_STRIPE_SIGNATURE=signature or signed(payload))

    def succeeded(self, amount=None, event_id="evt_1"):
        return event("payment_intent.succeeded", {
            "id": "pi_123", "object": "payment_intent", "amount_received": amount or self.order.total_cents,
            "metadata": {"order_number": self.order.number}}, event_id)

    def test_bad_signature_refused(self):
        response = self.post(self.succeeded(), signature="t=1,v1=bad")
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_payment_succeeded_marks_paid_once(self):
        self.assertEqual(self.post(self.succeeded()).status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(self.order.amount_received, self.order.total)
        sent = len(mail.outbox)
        self.post(self.succeeded())  # Stripe resends
        self.post(self.succeeded(event_id="evt_2"))  # or a second event
        self.assertEqual(len(mail.outbox), sent)
        self.assertEqual(WebhookEvent.objects.count(), 2)

    def test_amount_mismatch_tells_the_owner(self):
        self.post(self.succeeded(amount=100))
        self.assertTrue(any("does not match" in m.subject for m in mail.outbox))

    def test_unknown_payment_intent_ignored(self):
        body = event("payment_intent.succeeded", {"id": "pi_other", "amount_received": 5, "metadata": {}})
        self.assertEqual(self.post(body).status_code, 200)

    def test_return_page_marks_paid_if_the_webhook_is_slow(self):
        with mock.patch.object(payments.FakePayments, "payment_status",
                               return_value=("succeeded", self.order.total)):
            response = self.client.get(f"/checkout/complete/?payment_intent=pi_123")
        self.assertRedirects(response, self.order.get_absolute_url(), fetch_redirect_response=False)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)

    def test_return_page_after_a_failed_payment_goes_back_to_pay(self):
        with mock.patch.object(payments.FakePayments, "payment_status",
                               return_value=("requires_payment_method", Decimal("0"))):
            response = self.client.get("/checkout/complete/?payment_intent=pi_123")
        self.assertRedirects(response, "/checkout/pay/", fetch_redirect_response=False)

    def test_invoice_helpers_read_both_api_shapes(self):
        new = {"parent": {"subscription_details": {"subscription": "sub_1"}}}
        old = {"subscription": "sub_2"}
        self.assertEqual(webhooks._invoice_subscription_id(new), "sub_1")
        self.assertEqual(webhooks._invoice_subscription_id(old), "sub_2")
