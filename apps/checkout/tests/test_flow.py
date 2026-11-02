"""The cart and checkout through Django's test client, with the stand-in
payment and shipping providers: cart → address → shipping → pay → done."""

from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.test import override_settings
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.checkout.models import Cart, CheckoutSettings, DiscountCode, Order, TaxRate
from apps.checkout.orders import mark_shipped

from .helpers import ADDRESS, CheckoutTestCase, checkout_to_payment, form_data, load_catalog


class CartTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        self.tea, self.mug = load_catalog()

    def test_product_page_has_the_add_to_cart_form(self):
        page = self.client.get(self.tea.product.get_absolute_url())
        self.assertContains(page, 'action="/cart/add/"')
        self.assertContains(page, "Add to cart")
        self.assertNotContains(page, "Online ordering opens soon")

    @override_settings(PAYMENT_PROVIDER="stripe", STRIPE_SECRET_KEY="")
    def test_without_payments_set_up_the_product_page_says_so(self):
        page = self.client.get(self.tea.product.get_absolute_url())
        self.assertContains(page, "Online ordering opens soon")
        self.assertNotContains(page, "Add to cart")
        self.client.post("/cart/add/", {"size": self.tea.pk})
        self.assertTemplateUsed(self.client.get("/checkout/"), "checkout/closed.html")

    def test_add_update_and_remove(self):
        self.client.post("/cart/add/", {"size": self.tea.pk, "quantity": 2})
        self.client.post("/cart/add/", {"size": self.tea.pk, "quantity": 1})
        cart = Cart.objects.get()
        line = cart.lines.get()
        self.assertEqual(line.quantity, 3)
        page = self.client.get("/cart/")
        self.assertContains(page, self.tea.product.name)
        self.assertEqual(page.context["figures"].subtotal, self.tea.price * 3)
        self.client.post("/cart/update/", {f"quantity-{line.pk}": 1})
        self.assertEqual(cart.lines.get().quantity, 1)
        self.client.post("/cart/update/", {"remove": line.pk})
        self.assertFalse(cart.lines.exists())

    def test_quantity_is_limited_by_stock(self):
        # The demo stocks 12 of each piece of merchandise.
        self.client.post("/cart/add/", {"size": self.mug.pk, "quantity": 12})
        response = self.client.post("/cart/add/", {"size": self.mug.pk, "quantity": 5}, follow=True)
        self.assertEqual(Cart.objects.get().lines.get().quantity, 12)
        self.assertContains(response, "at a time")

    def test_header_counts_items(self):
        self.client.post("/cart/add/", {"size": self.tea.pk, "quantity": 2})
        self.assertContains(self.client.get("/"), "2<span class=\"visually-hidden\"> items")

    def test_inactive_size_cannot_be_added(self):
        self.tea.is_active = False
        self.tea.save()
        self.client.post("/cart/add/", {"size": self.tea.pk})
        self.assertFalse(Cart.objects.filter(lines__isnull=False).exists())

    def test_discount_code_applied_and_bad_code_refused(self):
        DiscountCode.objects.create(code="SPRING10", kind=DiscountCode.Kind.PERCENT, value=Decimal("10"))
        self.client.post("/cart/add/", {"size": self.tea.pk})
        response = self.client.post("/cart/discount/", form_data(code="nope"), follow=True)
        self.assertContains(response, "There is no discount code NOPE")
        self.client.post("/cart/discount/", form_data(code="spring10"))
        self.assertEqual(Cart.objects.get().discount.code, "SPRING10")

    def test_discount_form_refuses_bots(self):
        self.client.post("/cart/add/", {"size": self.tea.pk})
        DiscountCode.objects.create(code="X", kind=DiscountCode.Kind.FREE_SHIPPING)
        self.client.post("/cart/discount/", form_data(code="X", website="http://spam"))
        self.assertIsNone(Cart.objects.get().discount)
        self.client.post("/cart/discount/", {"code": "X"})  # no time stamp
        self.assertIsNone(Cart.objects.get().discount)

    @override_settings(STOREFRONT_OPEN=False)
    def test_closed_shop_hides_the_cart(self):
        self.assertEqual(self.client.get("/cart/").status_code, 404)
        self.assertEqual(self.client.post("/cart/add/", {"size": self.tea.pk}).status_code, 404)


class CheckoutTests(CheckoutTestCase):
    def setUp(self):
        super().setUp()
        self.tea, self.mug = load_catalog()
        TaxRate.objects.create(state="NY", zip_prefix="122", rate=Decimal("0.08"), jurisdiction="Albany County")

    def test_whole_checkout_with_a_mixed_order(self):
        self.client.post("/cart/add/", {"size": self.mug.pk})
        response = checkout_to_payment(self.client, self.tea, quantity=2)
        self.assertRedirects(response, "/checkout/pay/", fetch_redirect_response=False)
        order = Order.objects.get()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.email, "ada@example.com")
        self.assertEqual(order.ship_state, "NY")
        self.assertTrue(order.address_verified)
        items = self.tea.price * 2 + self.mug.price
        self.assertEqual(order.subtotal, items)
        share = (order.shipping_amount * self.mug.price / items).quantize(Decimal("0.01"))
        self.assertEqual(order.taxable_amount, self.mug.price + share)
        self.assertEqual(order.tax_amount, (order.taxable_amount * Decimal("0.08")).quantize(Decimal("0.01")))
        self.assertEqual(order.total, items + order.shipping_amount + order.tax_amount)
        self.assertEqual(order.lines.count(), 2)

        pay = self.client.get("/checkout/pay/")
        self.assertContains(pay, "Test mode")
        self.assertContains(pay, f"Pay ${order.total:,.2f}")
        done = self.client.post("/checkout/pay/test/", follow=True)
        self.assertContains(done, "Your order is in")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertIsNotNone(order.ship_by)
        self.assertIsNotNone(order.confirmation_sent_at)
        self.assertFalse(Cart.objects.exists())
        subjects = [m.subject for m in mail.outbox]
        self.assertIn(f"Your Teashop order {order.number}", subjects)
        self.assertIn(f"New order {order.number}: ${order.total:,.2f}", subjects)
        confirmation = next(m for m in mail.outbox if m.to == ["ada@example.com"])
        self.assertIn(order.get_absolute_url(), confirmation.body)
        self.assertIn("Sales tax (8% on", confirmation.body)
        self.assertTrue(AuditEvent.objects.filter(action="checkout.order_paid").exists())

    def test_paying_twice_does_nothing_more(self):
        checkout_to_payment(self.client, self.tea)
        self.client.post("/checkout/pay/test/")
        from apps.checkout.orders import mark_paid

        self.assertFalse(mark_paid(Order.objects.get()))
        self.assertEqual(len([m for m in mail.outbox if m.to == ["ada@example.com"]]), 1)

    def test_going_back_updates_the_same_order(self):
        checkout_to_payment(self.client, self.tea)
        first = Order.objects.get()
        page = self.client.get("/checkout/shipping/")
        priority = page.context["options"][1][0]
        self.client.post("/checkout/shipping/", {"rate": priority.id})
        self.assertEqual(Order.objects.count(), 1)
        first.refresh_from_db()
        self.assertEqual(first.shipping_service, "USPS Priority Mail")

    def test_tea_only_order_has_no_tax(self):
        checkout_to_payment(self.client, self.tea)
        self.assertEqual(Order.objects.get().tax_amount, Decimal("0"))

    def test_outside_contiguous_states_refused(self):
        self.client.post("/cart/add/", {"size": self.tea.pk})
        response = self.client.post("/checkout/", form_data(**{**ADDRESS, "state": "NY", "zip": "99501"}))
        self.assertContains(response, "48 contiguous states")
        response = self.client.post("/checkout/", form_data(**{**ADDRESS, "state": "HI"}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_free_shipping_threshold(self):
        settings_row = CheckoutSettings.current()
        settings_row.free_shipping_over = Decimal("1.00")
        settings_row.save()
        checkout_to_payment(self.client, self.tea)
        order = Order.objects.get()
        self.assertEqual(order.shipping_amount, Decimal("0"))
        self.assertGreater(order.shipping_cost, 0)

    def test_sold_out_while_in_cart_stops_the_order(self):
        self.client.post("/cart/add/", {"size": self.mug.pk, "quantity": 2})
        self.mug.bom_lines.get().item.lots.update(quantity_on_hand=1)
        self.client.post("/checkout/", form_data(**ADDRESS))
        page = self.client.get("/checkout/shipping/")
        response = self.client.post("/checkout/shipping/", {"rate": page.context["options"][0][0].id}, follow=True)
        self.assertContains(response, "Only 1 of")
        self.assertFalse(Order.objects.exists())

    def test_vacation_pause_closes_checkout_and_shows_the_notice(self):
        CheckoutSettings.objects.update_or_create(pk=1, defaults=dict(
            vacation_mode=True, vacation_pause_orders=True, vacation_message="Away until June 12.",
            vacation_ships_from=timezone.localdate() + timedelta(days=10)))
        self.client.post("/cart/add/", {"size": self.tea.pk})
        response = self.client.get("/checkout/")
        self.assertTemplateUsed(response, "checkout/closed.html")
        self.assertContains(response, "Away until June 12.")
        self.assertContains(self.client.get(self.tea.product.get_absolute_url()), "Away until June 12.")

    def test_vacation_without_pause_pushes_the_ship_date(self):
        back = timezone.localdate() + timedelta(days=20)
        CheckoutSettings.objects.update_or_create(pk=1, defaults=dict(vacation_mode=True, vacation_ships_from=back))
        checkout_to_payment(self.client, self.tea)
        self.client.post("/checkout/pay/test/")
        self.assertGreaterEqual(Order.objects.get().ship_by, back)

    @override_settings(CHECKOUT_RATE_LIMIT=2)
    def test_rate_limit(self):
        self.client.post("/cart/add/", {"size": self.tea.pk})
        bad = {**ADDRESS, "zip": "x"}
        for _ in range(2):
            self.client.post("/checkout/", form_data(**bad))
        response = self.client.post("/checkout/", form_data(**ADDRESS))
        self.assertContains(response, "Too many tries")

    def test_ship_by_skips_weekends(self):
        shop = CheckoutSettings(ship_within_days=3)
        friday = timezone.localdate()
        while friday.weekday() != 4:
            friday += timedelta(days=1)
        self.assertEqual(shop.ship_by(friday), friday + timedelta(days=5))  # Wednesday

    def test_order_page_needs_its_secret(self):
        checkout_to_payment(self.client, self.tea)
        order = Order.objects.get()
        self.assertEqual(self.client.get("/orders/not-the-token/").status_code, 404)
        self.assertContains(self.client.get(order.get_absolute_url()), order.number)

    def test_marking_shipped_emails_tracking(self):
        checkout_to_payment(self.client, self.tea)
        self.client.post("/checkout/pay/test/")
        order = Order.objects.get()
        mail.outbox.clear()
        self.assertTrue(mark_shipped(order, "9400111899223817364052"))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertIn("9400111899223817364052", mail.outbox[0].body)
        self.assertIn("tools.usps.com", mail.outbox[0].body)
