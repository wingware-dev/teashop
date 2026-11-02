"""Cart, checkout, accounts, subscriptions and policies in a real browser,
with the WCAG 2.2 AA checks and screenshots (apps/core/uitesting.py).  The
stand-in payment and shipping providers take the place of Stripe and
EasyPost, so no network or account is needed."""

import re
from decimal import Decimal

from django.core import mail
from django.core.cache import cache
from django.test import override_settings

from apps.checkout.models import DiscountCode, Order, Subscription, SubscriptionPlan, TaxRate
from apps.core.uitesting import BrowserTestCase
from apps.storefront import demo

from .helpers import CHECKOUT_TEST_SETTINGS

COMBOS = [("phone", "light"), ("desktop", "dark")]


@override_settings(**CHECKOUT_TEST_SETTINGS)
class CheckoutUITests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        demo.load(owner=self.owner()[0])
        TaxRate.objects.create(state="NY", zip_prefix="122", rate=Decimal("0.08"), jurisdiction="Albany County")

    def fill_address(self, page, zip_code="12207"):
        page.get_by_label("Email").fill("ada@example.com")
        page.get_by_label("Full name").fill("Ada Lovelace")
        page.get_by_label("Street address").fill("12 Main St")
        page.get_by_label("City").fill("Albany")
        page.get_by_label("State").select_option("NY")
        page.get_by_label("ZIP code").fill(zip_code)

    def test_checkout_from_product_page_to_paid_order(self):
        DiscountCode.objects.create(code="WELCOME", kind=DiscountCode.Kind.PERCENT, value=Decimal("10"))
        for viewport, theme in COMBOS:
            page = self.new_page(viewport, theme)
            page.goto(self.url("/products/glass-teapot/"))
            self.check_current(page, "product-buy-box")
            page.get_by_role("button", name=re.compile("Add to cart")).click()
            page.goto(self.url("/products/assam-second-flush/"))
            page.get_by_label("Quantity").fill("2")
            page.get_by_role("button", name="Add to cart").click()
            page.wait_for_url("**/cart/")
            page.get_by_label("Discount code").fill("welcome")
            page.get_by_role("button", name="Apply").click()
            page.get_by_role("button", name="Remove code").wait_for()
            self.check_current(page, "checkout-1-cart")

            page.get_by_role("link", name="Check out").click()
            page.get_by_role("button", name="Continue to shipping").click()
            self.assertGreater(page.locator(".field .error").count(), 0)
            self.check_current(page, "checkout-2-address-errors")
            self.fill_address(page)
            self.check_current(page, "checkout-2-address")
            page.get_by_role("button", name="Continue to shipping").click()
            page.wait_for_url("**/checkout/shipping/")
            self.check_current(page, "checkout-3-shipping")

            page.get_by_text("USPS Priority Mail", exact=True).click()
            page.get_by_role("button", name="Continue to payment").click()
            page.wait_for_url("**/checkout/pay/")
            self.check_current(page, "checkout-4-pay")
            page.get_by_role("button", name=re.compile(r"Pay \$.* \(test\)")).click()
            page.get_by_role("heading", name="Your order is in").wait_for()
            self.check_current(page, "checkout-5-done")

        orders = Order.objects.filter(status=Order.Status.PAID)
        self.assertEqual(orders.count(), 2)
        order = orders.first()
        self.assertEqual(order.shipping_service, "USPS Priority Mail")
        self.assertEqual(order.discount_code, "WELCOME")
        self.assertGreater(order.tax_amount, 0)  # the teapot is taxable

    def test_address_suggestion_and_closed_states(self):
        page = self.new_page("desktop", "light")
        page.goto(self.url("/products/assam-second-flush/"))
        page.get_by_role("button", name="Add to cart").click()
        page.goto(self.url("/checkout/"))
        self.fill_address(page, zip_code="99501")
        page.get_by_role("button", name="Continue to shipping").click()
        page.get_by_text("48 contiguous states").first.wait_for()
        self.check_current(page, "checkout-address-not-shipped")

    def test_account_pages(self):
        page = self.new_page("phone", "light")
        page.goto(self.url("/your-account/sign-in/"))
        self.check_current(page, "account-sign-in")
        page.get_by_label("Email").fill("ada@example.com")
        page.get_by_role("button", name="Email me a sign-in link").click()
        page.get_by_role("heading", name="Check your email").wait_for()
        self.check_current(page, "account-link-sent")
        link = re.search(r"/your-account/sign-in/\S+/", mail.outbox[-1].body).group(0)
        page.goto(self.url(link))
        self.check_current(page, "account-confirm-sign-in")
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("heading", name="Your account").wait_for()
        for viewport, theme in COMBOS:
            with self.subTest(viewport=viewport, theme=theme):
                page.set_viewport_size({"width": 390 if viewport == "phone" else 1280, "height": 844})
                page.emulate_media(color_scheme=theme)
                self.check_current(page, "account-home", viewport=viewport, theme=theme)

    def test_subscription_sign_up_and_one_step_cancel(self):
        plan = SubscriptionPlan.objects.create(
            name="Tea of the month", slug="tea-of-the-month", price=Decimal("24.00"), interval_months=1,
            description="Two 50 g pouches of teas we are excited about, a different pair each month.")
        self.check_page("/subscriptions/", "subscription-plans")
        page = self.new_page("phone", "dark")
        page.goto(self.url(plan.get_absolute_url()))
        self.check_current(page, "subscription-sign-up")
        self.fill_address(page)
        page.get_by_role("button", name="Subscribe and continue to payment").click()
        page.get_by_text("Tick the box to agree").wait_for()
        self.check_current(page, "subscription-no-consent")
        self.fill_address(page)
        page.get_by_label(re.compile("I agree to the automatic renewal terms")).check()
        page.get_by_role("button", name="Subscribe and continue to payment").click()
        page.wait_for_url("**/subscriptions/pay/**")
        self.check_current(page, "subscription-pay")
        page.get_by_role("button", name=re.compile("Subscribe and pay")).click()
        page.get_by_role("heading", name="You're subscribed").wait_for()
        self.check_current(page, "subscription-welcome")
        page.get_by_role("link", name="cancel this subscription").click()
        self.check_current(page, "subscription-cancel")
        page.get_by_role("button", name="Cancel my subscription").click()
        page.get_by_role("heading", name="Your subscription is cancelled").wait_for()
        self.check_current(page, "subscription-cancelled")
        self.assertEqual(Subscription.objects.get().status, Subscription.Status.CANCELLED)

    def test_policy_pages(self):
        for slug in ("privacy", "terms", "returns", "shipping", "subscriptions", "accessibility"):
            self.check_page(f"/policies/{slug}/", f"policy-{slug}")

    def test_empty_cart_and_owner_sales_report(self):
        self.check_page("/cart/", "checkout-cart-empty")
        self.check_page("/owner/checkout/sales-by-state/", "owner-sales-by-state", signed_in=True)
