"""Customer accounts: sign-in links, order history, buy again."""

import re
import time
from unittest import mock

from django.core import mail, signing
from django.test import override_settings

from apps.checkout import accounts
from apps.checkout.models import Cart, Customer, Order

from .helpers import CheckoutTestCase, checkout_to_payment, form_data, load_catalog


class SignInTests(CheckoutTestCase):
    def link(self):
        return re.search(r"http://\S+/your-account/sign-in/\S+/", mail.outbox[-1].body).group(0)

    def test_link_signs_in_once(self):
        response = self.client.post("/your-account/sign-in/", form_data(email="Ada@Example.com"))
        self.assertContains(response, "Check your email")
        path = self.link().split("localhost:8000")[1]
        # A GET (mail scanners open links) does not use the link up.
        self.assertContains(self.client.get(path), "Press the button")
        self.assertRedirects(self.client.post(path), "/your-account/", fetch_redirect_response=False)
        self.assertEqual(Customer.objects.get().email, "ada@example.com")
        self.assertContains(self.client.get("/your-account/"), "ada@example.com")
        other = self.client_class()
        response = other.post(path, follow=True)
        self.assertContains(response, "expired or was already used")

    def test_expired_link(self):
        token = accounts.sign_in_token("ada@example.com")
        with mock.patch("django.core.signing.time.time", return_value=time.time() + 3600):
            self.assertIsNone(accounts.redeem(token))

    def test_tampered_link(self):
        self.assertIsNone(accounts.redeem("garbage"))
        forged = signing.dumps({"e": "ada@example.com", "s": ""}, salt="other")
        self.assertIsNone(accounts.redeem(forged))

    def test_same_answer_for_any_email_and_rate_limited(self):
        with override_settings(SIGN_IN_RATE_LIMIT=2):
            for _ in range(2):
                self.client.post("/your-account/sign-in/", form_data(email="ada@example.com"))
            response = self.client.post("/your-account/sign-in/", form_data(email="ada@example.com"))
        self.assertContains(response, "Too many tries")
        self.assertEqual(len(mail.outbox), 2)

    def test_account_needs_sign_in(self):
        self.assertRedirects(self.client.get("/your-account/"), "/your-account/sign-in/",
                             fetch_redirect_response=False)


class HistoryTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        self.tea, self.mug = load_catalog()
        self.client.post("/cart/add/", {"size": self.mug.pk})
        checkout_to_payment(self.client, self.tea, quantity=2)
        self.client.post("/checkout/pay/test/")
        self.order = Order.objects.get()

    def sign_in(self):
        customer = accounts.redeem(accounts.sign_in_token("ada@example.com"))
        session = self.client.session
        session[accounts.SESSION_KEY] = customer.pk
        session.save()
        return customer

    def test_guest_orders_show_after_signing_in(self):
        customer = self.sign_in()
        self.order.refresh_from_db()
        self.assertEqual(self.order.customer, customer)
        page = self.client.get("/your-account/")
        self.assertContains(page, self.order.number)
        self.assertContains(page, "Buy again")

    def test_buy_again_fills_the_cart(self):
        self.sign_in()
        self.client.post(f"/your-account/orders/{self.order.number}/buy-again/")
        cart = Cart.objects.get()
        self.assertEqual({(l.size_option_id, l.quantity) for l in cart.lines.all()},
                         {(self.tea.pk, 2), (self.mug.pk, 1)})

    def test_buy_again_skips_what_is_no_longer_sold(self):
        self.sign_in()
        self.mug.is_active = False
        self.mug.save()
        response = self.client.post(f"/your-account/orders/{self.order.number}/buy-again/", follow=True)
        self.assertContains(response, "1 item from that order is no longer sold")
        self.assertEqual(Cart.objects.get().lines.count(), 1)

    def test_others_orders_are_not_reachable(self):
        customer = self.sign_in()
        Order.objects.filter(pk=self.order.pk).update(email="bob@example.com", customer=None)
        response = self.client.post(f"/your-account/orders/{self.order.number}/buy-again/")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(self.order, customer.orders())

    def test_signed_in_checkout_prefills_and_saves_the_address(self):
        customer = self.sign_in()
        self.client.post("/cart/add/", {"size": self.tea.pk})
        page = self.client.get("/checkout/")
        self.assertEqual(page.context["form"].initial["email"], "ada@example.com")
        data = form_data(email="ada@example.com", name="Ada L", street1="5 Oak Ave", street2="", city="Troy",
                         state="NY", zip="12180", phone="", save_address="1")
        self.client.post("/checkout/", data)
        customer.refresh_from_db()
        self.assertEqual((customer.ship_street1, customer.ship_zip), ("5 OAK AVE", "12180"))

