"""Subscriptions under NY GBL 527-a and California's automatic renewal
law: terms beside the button, explicit consent, acknowledgment email,
reminders before yearly renewals, one-step online cancellation."""

import re
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from apps.checkout import payments, subscriptions, webhooks
from apps.checkout.models import Order, Subscription, SubscriptionPlan
from apps.checkout.payments import StripePayments

from .helpers import ADDRESS, CheckoutTestCase, form_data


def make_plan(months=1, price="24.00"):
    return SubscriptionPlan.objects.create(name="Tea of the month", slug=f"monthly-{months}",
                                           description="Two 50 g pouches of the month's teas.",
                                           price=Decimal(price), interval_months=months)


class SignUpTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        self.plan = make_plan()

    def test_terms_sit_next_to_the_button_with_a_consent_box(self):
        page = self.client.get(self.plan.get_absolute_url())
        html = page.content.decode()
        terms = html.index("renews automatically every month")
        consent = html.index('name="consent"')
        button = html.index("Subscribe and continue to payment")
        self.assertLess(terms, consent)
        self.assertLess(consent, button)
        self.assertLess(button - terms, 2500, "the terms must be right by the button")
        self.assertIn("$24.00", html[terms - 400:button])
        self.assertIn("Cancel any time online", html)

    def test_no_consent_no_subscription(self):
        response = self.client.post(self.plan.get_absolute_url(), form_data(**ADDRESS))
        self.assertContains(response, "Tick the box to agree")
        self.assertFalse(Subscription.objects.exists())

    def test_sign_up_pay_acknowledge(self):
        response = self.client.post(self.plan.get_absolute_url(), form_data(**ADDRESS, consent="on"))
        subscription = Subscription.objects.get()
        self.assertRedirects(response, f"/subscriptions/pay/{subscription.token}/", fetch_redirect_response=False)
        self.assertEqual(subscription.status, Subscription.Status.PENDING)
        self.assertEqual(subscription.terms_text, self.plan.renewal_terms())
        self.assertIsNotNone(subscription.consented_at)
        self.assertContains(self.client.get(response.url), "Test mode")
        self.client.post(f"/subscriptions/pay/{subscription.token}/test/")
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertIsNotNone(subscription.acknowledgment_sent_at)
        order = Order.objects.get(subscription=subscription)
        self.assertEqual((order.status, order.total, order.tax_amount), (Order.Status.PAID, Decimal("24.00"), 0))
        ack = next(m for m in mail.outbox if "terms and how to cancel" in m.subject)
        self.assertIn(subscription.terms_text, ack.body.replace("\n", " ").replace("  ", "  "))
        self.assertIn(subscription.cancel_url(), ack.body)

    def test_only_the_signing_up_browser_can_pay(self):
        self.client.post(self.plan.get_absolute_url(), form_data(**ADDRESS, consent="on"))
        subscription = Subscription.objects.get()
        other = self.client_class()
        self.assertEqual(other.get(f"/subscriptions/pay/{subscription.token}/").status_code, 404)

    def test_renewal_terms_text(self):
        yearly = make_plan(12, "200.00")
        self.assertIn("every year", yearly.renewal_terms())
        self.assertIn("$200.00", yearly.renewal_terms())


class CancelTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        self.plan = make_plan()
        self.client.post(self.plan.get_absolute_url(), form_data(**ADDRESS, consent="on"))
        token = Subscription.objects.get().token
        self.client.post(f"/subscriptions/pay/{token}/test/")
        self.subscription = Subscription.objects.get()
        mail.outbox.clear()

    def test_one_step_cancel_from_the_email_link_without_signing_in(self):
        anonymous = self.client_class()
        page = anonymous.get(self.subscription.cancel_url())
        self.assertEqual(len(re.findall(r"<button", page.content.decode().split("<main")[1])), 1)
        anonymous.post(self.subscription.cancel_url())
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.CANCELLED)
        self.assertIn("is cancelled", mail.outbox[0].subject)
        self.assertContains(anonymous.get(self.subscription.cancel_url()), "You will not be charged again")

    def test_cancel_works_even_while_the_shop_is_closed(self):
        with override_settings(STOREFRONT_OPEN=False):
            self.client.post(self.subscription.cancel_url())
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.CANCELLED)

    def test_stripe_subscription_stops_renewing(self):
        self.subscription.payment_provider = "stripe"
        self.subscription.stripe_subscription_id = "sub_1"
        self.subscription.save()
        client = mock.Mock()
        with mock.patch("apps.checkout.payments.provider", return_value=StripePayments(client)):
            subscriptions.cancel(self.subscription)
        client.v1.subscriptions.update.assert_called_once_with("sub_1", params={"cancel_at_period_end": True})


class RenewalTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        self.plan = make_plan(12, "200.00")
        self.subscription = Subscription.objects.create(
            plan=self.plan, email="ada@example.com", price=self.plan.price, interval_months=12,
            terms_text=self.plan.renewal_terms(), consented_at=timezone.now(), status=Subscription.Status.ACTIVE,
            payment_provider="stripe", stripe_subscription_id="sub_1", ship_name="Ada", ship_street1="1 Main St",
            ship_city="Albany", ship_state="NY", ship_zip="12207")

    def at(self, days):
        self.subscription.current_period_end = timezone.now() + timedelta(days=days)
        self.subscription.save()

    def test_reminder_inside_the_window_once(self):
        self.at(29)
        out = StringIO()
        call_command("send_subscription_reminders", stdout=out)
        self.assertIn("Queued 1", out.getvalue())
        self.assertIn("renews on", mail.outbox[0].subject)
        self.assertIn(self.subscription.cancel_url(), mail.outbox[0].body)
        call_command("send_subscription_reminders", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)

    def test_no_reminder_too_early_or_for_monthly_terms(self):
        self.at(40)
        self.assertEqual(subscriptions.send_reminders(), 0)
        self.subscription.interval_months = 1
        self.at(20)
        self.assertEqual(subscriptions.send_reminders(), 0)

    def test_missed_reminder_is_flagged(self):
        self.at(10)
        self.assertEqual(subscriptions.reminders_overdue(), [self.subscription])

    def test_renewal_invoice_makes_a_delivery_order(self):
        end = int((timezone.now() + timedelta(days=365)).timestamp())
        invoice = {"id": "in_2", "billing_reason": "subscription_cycle", "amount_paid": 20000,
                   "parent": {"subscription_details": {"subscription": "sub_1"}},
                   "lines": {"data": [{"period": {"end": end}}]}}
        webhooks.handle({"type": "invoice.paid", "data": {"object": invoice}})
        webhooks.handle({"type": "invoice.paid", "data": {"object": invoice}})  # resent
        order = Order.objects.get(subscription=self.subscription)
        self.assertEqual(order.total, Decimal("200.00"))
        self.assertEqual(int(self.subscription.__class__.objects.get().current_period_end.timestamp()), end)

    def test_failed_renewal_tells_the_customer(self):
        invoice = {"id": "in_3", "subscription": "sub_1"}
        webhooks.handle({"type": "invoice.payment_failed", "data": {"object": invoice}})
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.PAST_DUE)
        self.assertIn("did not go through", mail.outbox[0].subject)

    def test_stripe_cancellation_ends_it(self):
        webhooks.handle({"type": "customer.subscription.deleted",
                         "data": {"object": {"id": "sub_1", "status": "canceled", "items": {"data": []}}}})
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.ENDED)

    def test_stripe_subscription_request(self):
        client = mock.Mock()
        client.v1.customers.create.return_value = mock.Mock(id="cus_1")
        client.v1.products.create.return_value = mock.Mock(id="prod_1")
        created = mock.Mock(id="sub_9")
        created.latest_invoice.confirmation_secret.client_secret = "secret"
        client.v1.subscriptions.create.return_value = created
        started = StripePayments(client).start_subscription(self.subscription)
        params = client.v1.subscriptions.create.call_args.kwargs["params"]
        self.assertEqual(params["payment_behavior"], "default_incomplete")
        self.assertEqual(params["items"][0]["price_data"]["recurring"], {"interval": "year", "interval_count": 1})
        self.assertEqual(params["items"][0]["price_data"]["unit_amount"], 20000)
        self.assertEqual((started.id, started.client_secret, started.customer_id), ("sub_9", "secret", "cus_1"))
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.stripe_product_id, "prod_1")


def stripe_object(data):
    """A stand-in for a Stripe object: the shop reads them through to_dict()."""
    found = mock.Mock(**{k: v for k, v in data.items() if k != "to_dict"})
    found.to_dict.return_value = data
    return found


class CardUpdateTests(CheckoutTestCase):
    """A subscriber whose renewal failed saves a new card on the shop's own
    card page (a Stripe SetupIntent), and the renewal is retried on it."""

    def setUp(self):
        super().setUp()
        self.plan = make_plan()
        self.client.post(self.plan.get_absolute_url(), form_data(**ADDRESS, consent="on"))
        token = Subscription.objects.get().token
        self.client.post(f"/subscriptions/pay/{token}/test/")
        self.subscription = Subscription.objects.get()
        mail.outbox.clear()

    def stripe_billed(self, status=Subscription.Status.PAST_DUE):
        self.subscription.payment_provider = "stripe"
        self.subscription.stripe_subscription_id = "sub_1"
        self.subscription.stripe_customer_id = "cus_1"
        self.subscription.status = status
        self.subscription.save()

    def stripe_mock(self, intent_status="succeeded", subscription_id=None, customer="cus_1",
                    default_card=None, invoice_status="open"):
        client = mock.Mock()
        client.v1.setup_intents.create.return_value = mock.Mock(id="seti_1", client_secret="seti_1_secret")
        client.v1.setup_intents.retrieve.return_value = stripe_object({
            "id": "seti_1", "status": intent_status, "customer": customer, "payment_method": "pm_new",
            "metadata": {"subscription": str(subscription_id or self.subscription.pk), "purpose": "card_update"}})
        client.v1.subscriptions.retrieve.return_value = stripe_object({
            "id": "sub_1", "default_payment_method": default_card,
            "latest_invoice": {"id": "in_7", "status": invoice_status}})
        client.v1.invoices.pay.return_value = mock.Mock(status="paid")
        return client

    def test_failed_renewal_email_links_to_the_card_page(self):
        self.subscription.status = Subscription.Status.ACTIVE
        subscriptions.payment_failed(self.subscription)
        body = mail.outbox[0].body
        self.assertIn(f"/subscriptions/card/{self.subscription.token}/", body)
        self.assertIn(self.subscription.cancel_url(), body)

    def test_stand_in_card_pays_the_missed_renewal_without_signing_in(self):
        subscriptions.payment_failed(self.subscription)
        anonymous = self.client_class()
        page = anonymous.get(self.subscription.card_url())
        self.assertContains(page, "Update your card")
        self.assertContains(page, "Save card and pay (test)")
        page = anonymous.post(f"/subscriptions/card/{self.subscription.token}/test/")
        self.assertContains(page, "Thank you: your card is updated")
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(Order.objects.filter(subscription=self.subscription).count(), 2)

    def test_active_subscription_changes_card_without_a_charge(self):
        page = self.client.get(self.subscription.card_url())
        self.assertContains(page, "Nothing is charged today")
        page = self.client.post(f"/subscriptions/card/{self.subscription.token}/test/")
        self.assertContains(page, "Your card is updated")
        self.assertEqual(Order.objects.filter(subscription=self.subscription).count(), 1)

    def test_no_card_form_for_a_cancelled_subscription(self):
        subscriptions.cancel(self.subscription)
        page = self.client.get(self.subscription.card_url())
        self.assertContains(page, "There is no card to update")
        self.assertNotContains(page, "payment-form")
        self.client.post(f"/subscriptions/card/{self.subscription.token}/test/")
        self.assertEqual(Order.objects.filter(subscription=self.subscription).count(), 1)

    def test_stripe_billed_subscription_needs_stripe_configured(self):
        self.stripe_billed()
        page = self.client.get(self.subscription.card_url())
        self.assertContains(page, "We can't change this subscription's card online")
        self.assertNotContains(page, "payment-form")

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_PUBLISHABLE_KEY="pk_test_x", PAYMENT_PROVIDER="stripe")
    def test_stripe_card_page_shows_the_payment_element_for_a_setup_intent(self):
        self.stripe_billed()
        client = self.stripe_mock()
        with mock.patch("apps.checkout.payments.stripe_client", return_value=client):
            page = self.client.get(self.subscription.card_url())
        html = page.content.decode()
        self.assertIn('data-client-secret="seti_1_secret"', html)
        self.assertIn('data-intent="setup"', html)
        self.assertIn(f"/subscriptions/card/{self.subscription.token}/done/", html)
        params = client.v1.setup_intents.create.call_args.kwargs["params"]
        self.assertEqual(params["customer"], "cus_1")
        self.assertEqual(params["usage"], "off_session")
        self.assertEqual(params["metadata"], {"subscription": str(self.subscription.pk), "purpose": "card_update"})

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_PUBLISHABLE_KEY="pk_test_x", PAYMENT_PROVIDER="stripe")
    def test_stripe_return_page_sets_the_card_and_retries_the_renewal(self):
        self.stripe_billed()
        client = self.stripe_mock()
        with mock.patch("apps.checkout.payments.stripe_client", return_value=client):
            page = self.client.get(f"/subscriptions/card/{self.subscription.token}/done/?setup_intent=seti_1")
        self.assertContains(page, "Thank you: your card is updated")
        client.v1.subscriptions.update.assert_called_once_with("sub_1", params={"default_payment_method": "pm_new"})
        client.v1.customers.update.assert_called_once_with(
            "cus_1", params={"invoice_settings": {"default_payment_method": "pm_new"}})
        client.v1.invoices.pay.assert_called_once_with("in_7", params={"payment_method": "pm_new"})

    def test_stripe_repeat_changes_nothing(self):
        self.stripe_billed(Subscription.Status.ACTIVE)
        client = self.stripe_mock(default_card="pm_new", invoice_status="paid")
        result = StripePayments(client).finish_card_update(self.subscription, "seti_1")
        self.assertEqual(result, payments.CardUpdate.SAVED)
        client.v1.subscriptions.update.assert_not_called()
        client.v1.invoices.pay.assert_not_called()

    def test_stripe_setup_intent_for_another_subscription_is_refused(self):
        self.stripe_billed()
        for client in (self.stripe_mock(subscription_id=self.subscription.pk + 1), self.stripe_mock(customer="cus_2")):
            result = StripePayments(client).finish_card_update(self.subscription, "seti_1")
            self.assertEqual(result, payments.CardUpdate.FAILED)
            client.v1.subscriptions.update.assert_not_called()

    def test_stripe_unconfirmed_card_is_not_used(self):
        self.stripe_billed()
        for status, expected in (("requires_payment_method", payments.CardUpdate.FAILED),
                                 ("processing", payments.CardUpdate.PROCESSING)):
            client = self.stripe_mock(intent_status=status)
            self.assertEqual(StripePayments(client).finish_card_update(self.subscription, "seti_1"), expected)
            client.v1.subscriptions.update.assert_not_called()

    def test_stripe_declined_retry(self):
        import stripe

        self.stripe_billed()
        client = self.stripe_mock()
        client.v1.invoices.pay.side_effect = stripe.CardError("Your card was declined.", None, "card_declined")
        self.assertEqual(StripePayments(client).finish_card_update(self.subscription, "seti_1"),
                         payments.CardUpdate.DECLINED)
        client.v1.subscriptions.update.assert_called_once()

    def test_stripe_unreachable_becomes_a_customer_message(self):
        import stripe

        self.stripe_billed()
        client = self.stripe_mock()
        client.v1.setup_intents.create.side_effect = stripe.APIConnectionError("down")
        with self.assertRaises(payments.PaymentError):
            StripePayments(client).start_card_update(self.subscription)

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", PAYMENT_PROVIDER="stripe")
    def test_setup_intent_webhook_finishes_the_change(self):
        self.stripe_billed()
        client = self.stripe_mock()
        obj = {"id": "seti_1", "metadata": {"subscription": str(self.subscription.pk), "purpose": "card_update"}}
        with mock.patch("apps.checkout.payments.stripe_client", return_value=client):
            webhooks.handle({"type": "setup_intent.succeeded", "data": {"object": obj}})
            webhooks.handle({"type": "setup_intent.succeeded",
                             "data": {"object": {"id": "seti_2", "metadata": {}}}})
        client.v1.setup_intents.retrieve.assert_called_once_with("seti_1")
        client.v1.invoices.pay.assert_called_once()
