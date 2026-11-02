"""Packing, labels, cancellations, refunds, reships, delay notices and
pickups, with the stand-in carrier and payments."""

import importlib
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.apps import apps as django_apps
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.audit import acting_as_agent
from apps.catalog.models import SoldPackage
from apps.checkout import tax as checkout_tax
from apps.checkout.models import Order
from apps.checkout.shipping import Address
from apps.inventory.models import Item, Lot, StockMovement
from apps.fulfillment import boxes, services, summary
from apps.fulfillment.models import BoxSize, DelayNotice, PackageDimensions, Parcel, Pickup, Refund
from apps.fulfillment.testing import TEST_SETTINGS, paid_order, shop, size


@override_settings(**TEST_SETTINGS)
class FulfillmentTestCase(TestCase):
    def setUp(self):
        self.scale = shop()
        self.assam = size("assam-second-flush")
        self.vanilla = size("vanilla-almond-black")
        self.teapot = size("glass-teapot")

    def pack_all(self, order, grams_over=Decimal("0.4")):
        packed = []
        for parcel in services.active_parcels(order):
            for row in services.progress(parcel):
                for _ in range(row.remaining):
                    grams = row.size.net_grams + grams_over if row.size.net_grams else None
                    packed.append(services.pack_package(parcel, row.order_line, measured_grams=grams,
                                                        scale=self.scale, allergens_confirmed=True))
        return packed

    def ship(self, order, **kwargs):
        parcel = services.active_parcels(order)[0]
        suggestion = services.suggest_box(parcel)
        kwargs.setdefault("box", suggestion.box)
        return services.buy_label(parcel, weight_grams=kwargs.pop("weight_grams", 300),
                                  service=order.shipping_service, **kwargs)


class PackingTests(FulfillmentTestCase):
    def test_pack_records_weight_scale_and_takes_stock(self):
        order = paid_order([(self.assam, 2)])
        tea = self.assam.product.tea
        before = tea.on_hand()
        parcel = services.parcels(order)[0]
        line = order.lines.get()
        packed = services.pack_package(parcel, line, measured_grams=Decimal("50.3"), scale=self.scale)
        self.assertEqual(packed.measured_grams, Decimal("50.3"))
        self.assertEqual(packed.scale_serial, "SN-4471")
        self.assertEqual(packed.scale_sealed_on, self.scale.sealed_on)
        self.assertEqual(packed.sold_package.order_reference, order.number)
        self.assertEqual(packed.sold_package.tea_grams, 51)  # whole grams, rounded up, leave the lot
        self.assertEqual(tea.on_hand(), before - 51)
        self.assertEqual(services.progress(parcel)[0].remaining, 1)
        # The package's price is the line's, after its share of any discount.
        self.assertEqual(packed.sold_package.amount, self.assam.price)

    def test_under_weight_is_refused(self):
        order = paid_order([(self.assam, 1)])
        parcel = services.parcels(order)[0]
        with self.assertRaisesMessage(services.FulfillmentError, "under the labelled"):
            services.pack_package(parcel, order.lines.get(), measured_grams=Decimal("49.9"), scale=self.scale)
        self.assertFalse(SoldPackage.objects.exists())

    def test_broken_seal_or_no_scale_is_refused(self):
        order = paid_order([(self.assam, 1)])
        parcel = services.parcels(order)[0]
        with self.assertRaisesMessage(services.FulfillmentError, "Choose the scale"):
            services.pack_package(parcel, order.lines.get(), measured_grams=50)
        self.scale.seal_intact = False
        self.scale.save()
        with self.assertRaisesMessage(services.FulfillmentError, "seal is broken"):
            services.pack_package(parcel, order.lines.get(), measured_grams=50, scale=self.scale)

    def test_allergen_tea_needs_confirmation(self):
        order = paid_order([(self.vanilla, 1)])
        parcel = services.parcels(order)[0]
        with self.assertRaises(services.AllergenCheckNeeded) as caught:
            services.pack_package(parcel, order.lines.get(), measured_grams=50, scale=self.scale)
        self.assertEqual(caught.exception.allergens, ["Tree nuts"])
        packed = services.pack_package(parcel, order.lines.get(), measured_grams=50, scale=self.scale,
                                       allergens_confirmed=True)
        self.assertTrue(packed.allergens_confirmed)

    def test_cannot_pack_more_than_ordered(self):
        order = paid_order([(self.teapot, 1)])
        parcel = services.parcels(order)[0]
        services.pack_package(parcel, order.lines.get())
        with self.assertRaisesMessage(services.FulfillmentError, "packed already"):
            services.pack_package(parcel, order.lines.get())

    def test_unpack_puts_stock_back(self):
        order = paid_order([(self.assam, 1)])
        tea, pouch = self.assam.product.tea, Item.objects.get(code="POUCH")
        tea_before, pouch_before = tea.on_hand(), pouch.on_hand()
        packed = self.pack_all(order)[0]
        services.unpack(packed, "Wrong pouch")
        self.assertEqual((tea.on_hand(), pouch.on_hand()), (tea_before, pouch_before))
        self.assertTrue(StockMovement.objects.filter(reason=StockMovement.Reason.RETURNED, reference=order.number,
                                                     note="Wrong pouch").exists())
        self.assertEqual(services.progress(services.parcels(order)[0])[0].remaining, 1)


class BoxTests(FulfillmentTestCase):
    def test_smallest_box_in_stock(self):
        small = BoxSize.objects.get(item__code="BOX-S")
        self.assertEqual(boxes.suggest([(self.assam, 2)]).box, small)
        tin = size("earl-grey-cornflower", 100)
        self.assertEqual(boxes.suggest([(tin, 6)]).box, BoxSize.objects.get(item__code="BOX-L"))

    def test_every_package_must_fit_not_only_the_longest(self):
        # A long, flat pouch and a shorter but thicker tin: the 1.5 in mailer
        # takes the pouch but not the tin.
        tin = size("earl-grey-cornflower", 100)
        PackageDimensions.objects.create(size_option=self.assam, length_in=Decimal("6"), width_in=Decimal("4"),
                                         height_in=Decimal("1.5"))
        PackageDimensions.objects.create(size_option=tin, length_in=Decimal("3"), width_in=Decimal("2.75"),
                                         height_in=Decimal("2.75"))
        small = BoxSize.objects.get(item__code="BOX-S")
        mailer_item = Item.objects.create(code="MAILER", name="Padded mailer", kind=Item.Kind.SHIPPING_BOX)
        Lot.objects.create(item=mailer_item, quantity_received=20, supplier=small.item.lots.get().supplier)
        mailer = BoxSize.objects.create(item=mailer_item, length_in=Decimal("9"), width_in=Decimal("6"),
                                        height_in=Decimal("1.5"), empty_grams=20)
        self.assertEqual(boxes.suggest([(self.assam, 1)]).box, mailer)
        suggestion = boxes.suggest([(self.assam, 1), (tin, 1)])
        self.assertEqual(suggestion.biggest, [Decimal("6"), Decimal("4"), Decimal("2.75")])
        self.assertNotIn(mailer, suggestion.fitting)
        self.assertEqual(suggestion.box, small)

    def test_nothing_fits(self):
        suggestion = boxes.suggest([(self.teapot, 9)])
        self.assertIsNone(suggestion.box)
        self.assertIn("No box on your list holds it all", suggestion.note)

    def test_out_of_stock_box_is_suggested_only_with_a_warning(self):
        small = BoxSize.objects.get(item__code="BOX-S")
        lot = small.item.lots.get()
        from apps.inventory import services as inventory

        inventory.adjust(lot, -lot.quantity_on_hand, StockMovement.Reason.COUNT)
        suggestion = boxes.suggest([(self.assam, 1)])
        self.assertEqual(suggestion.box, BoxSize.objects.get(item__code="BOX-L"))


class LabelPurchaseTests(FulfillmentTestCase):
    def test_label_ships_the_order_takes_the_box_and_emails_tracking(self):
        order = paid_order([(self.assam, 2)])
        self.pack_all(order)
        small = BoxSize.objects.get(item__code="BOX-S")
        boxes_before, filler_before = small.item.on_hand(), small.filler.on_hand()
        label, warnings = self.ship(order)
        self.assertEqual(warnings, [])
        self.assertTrue(label.test_mode)
        self.assertTrue(label.label_file.read().startswith(b"%PDF"))
        self.assertEqual(small.item.on_hand(), boxes_before - 1)
        self.assertEqual(small.filler.on_hand(), filler_before - 1)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertEqual(order.tracking_number, label.tracking_number)
        self.assertTrue(any(label.tracking_number in m.body for m in mail.outbox if m.to == [order.email]))

    def test_not_everything_packed(self):
        order = paid_order([(self.assam, 1), (self.teapot, 1)])
        parcel = services.parcels(order)[0]
        services.pack_package(parcel, order.lines.get(size_option=self.teapot))
        with self.assertRaisesMessage(services.FulfillmentError, "Not everything is packed"):
            self.ship(order)

    def test_ship_part_back_orders_the_rest(self):
        order = paid_order([(self.assam, 1), (self.teapot, 1)])
        parcel = services.parcels(order)[0]
        services.pack_package(parcel, order.lines.get(size_option=self.teapot))
        label, _ = self.ship(order, ship_partial=True)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        backorder = order.parcels.get(status=Parcel.Status.BACKORDERED)
        self.assertEqual([(line.order_line.size_option, line.quantity) for line in backorder.lines.all()],
                         [(self.assam, 1)])
        self.assertIn("Part of your", mail.outbox[-1].subject)
        # The rest ships later and completes the order.
        services.resume(backorder)
        self.pack_all(order)
        services.buy_label(backorder, weight_grams=200, service=order.shipping_service,
                           box=BoxSize.objects.get(item__code="BOX-S"))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)

    def test_void_returns_the_box_and_reopens(self):
        order = paid_order([(self.assam, 1)])
        self.pack_all(order)
        small = BoxSize.objects.get(item__code="BOX-S")
        before = small.item.on_hand()
        label, _ = self.ship(order)
        services.void_label(label)
        self.assertEqual(small.item.on_hand(), before)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(label.parcel.status, Parcel.Status.OPEN)
        with self.assertRaisesMessage(services.FulfillmentError, "already voided"):
            services.void_label(label)

    def test_other_box_needs_a_description(self):
        order = paid_order([(self.assam, 1)])
        self.pack_all(order)
        with self.assertRaisesMessage(services.FulfillmentError, "describe the one you used"):
            self.ship(order, box=None)
        label, _ = self.ship(order, box=None, box_description="Reused shoe box",
                             dimensions=[Decimal(12), Decimal(7), Decimal(4)])
        self.assertEqual(label.box_text, "Reused shoe box")


class CancelAndRefundTests(FulfillmentTestCase):
    def test_cancel_puts_stock_back_and_refunds_everything(self):
        order = paid_order([(self.assam, 1), (self.teapot, 1)])
        tea = self.assam.product.tea
        before = tea.on_hand()
        self.pack_all(order)
        amount = services.cancel_order(order, "Customer asked")
        self.assertEqual(amount, order.total)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(tea.on_hand(), before)
        self.assertFalse(SoldPackage.objects.filter(order_reference=order.number, reversed_at=None).exists())
        self.assertEqual(Refund.objects.get(order=order).kind, Refund.Kind.CANCELLATION)
        self.assertIn("is cancelled", mail.outbox[-1].subject)

    def test_shipped_order_cannot_be_cancelled(self):
        order = paid_order([(self.assam, 1)])
        self.pack_all(order)
        self.ship(order)
        order.refresh_from_db()
        with self.assertRaisesMessage(services.FulfillmentError, "Refund a shipped order instead"):
            services.cancel_order(order, "Too late")

    def test_partial_refunds_up_to_what_was_paid(self):
        order = paid_order([(self.assam, 2)])
        services.refund(order, Decimal("5.00"), "Dented tin")
        self.assertEqual(services.refundable(order), order.total - Decimal("5.00"))
        with self.assertRaisesMessage(services.FulfillmentError, "At most"):
            services.refund(order, order.total, "Too much")
        self.assertIn("A refund", mail.outbox[-1].subject)

    def test_agents_cannot_refund(self):
        order = paid_order([(self.assam, 1)])
        with acting_as_agent("support-agent"), self.assertRaises(PermissionDenied):
            services.refund(order, Decimal("1.00"), "Sorry")


def taxed(order, rate=Decimal("0.08")):
    """order with New York tax at rate on its teapot and its share of the
    shipping, as checkout charges it."""
    goods, shipping = checkout_tax.taxable_base([(line.net_amount, line.taxable) for line in order.lines.all()],
                                                order.shipping_amount)
    order.taxable_amount = goods + shipping
    order.tax_amount = checkout_tax.money(order.taxable_amount * rate)
    order.tax_rate = rate
    order.total += order.tax_amount
    order.amount_received = order.total
    order.save()
    return order


class RefundTaxTests(FulfillmentTestCase):
    """Each refund records the taxable amount and tax it gives back, from
    what it is for."""

    def setUp(self):
        super().setUp()
        self.order = taxed(paid_order([(self.assam, 1), (self.teapot, 1)]))
        self.tea = self.order.lines.get(taxable=False)
        self.pot = self.order.lines.get(taxable=True)

    def test_refunding_tea_gives_back_no_tax(self):
        refund = services.refund(self.order, self.tea.net_amount, "Stale", items={self.tea: 1})
        self.assertEqual((refund.taxable_amount, refund.tax_amount), (Decimal("0.00"), Decimal("0.00")))

    def test_refunding_merchandise_gives_back_its_tax(self):
        refund = services.refund(self.order, Decimal("30.24"), "Broken", items={self.pot: 1})
        self.assertEqual((refund.taxable_amount, refund.tax_amount), (Decimal("28.00"), Decimal("2.24")))

    def test_part_of_an_item_gives_back_that_part_of_its_tax(self):
        refund = services.refund(self.order, Decimal("15.12"), "Chipped lid", items={self.pot: 1})
        self.assertEqual((refund.taxable_amount, refund.tax_amount), (Decimal("14.00"), Decimal("1.12")))

    def test_shipping_gives_back_the_tax_on_its_taxable_share(self):
        _, share = checkout_tax.taxable_base([(self.tea.net_amount, False), (self.pot.net_amount, True)],
                                             self.order.shipping_amount)
        tax = checkout_tax.money(share * Decimal("0.08"))
        refund = services.refund(self.order, self.order.shipping_amount + tax, "Late", shipping=True)
        self.assertEqual((refund.taxable_amount, refund.tax_amount), (share, tax))

    def test_no_more_than_what_was_ticked(self):
        with mock.patch.object(services, "_payment_provider") as provider, \
                self.assertRaisesMessage(services.FulfillmentError, "more than what you ticked"):
            services.refund(self.order, self.tea.net_amount + Decimal("0.01"), "Stale", items={self.tea: 1})
        provider.assert_not_called()
        self.assertFalse(Refund.objects.exists())

    def test_items_of_another_order_are_refused(self):
        other = paid_order([(self.assam, 1)])
        with self.assertRaisesMessage(services.FulfillmentError, "not in this order"):
            services.refund(self.order, Decimal("1.00"), "Mixed up", items={other.lines.get(): 1})

    def test_the_rest_refunded_gives_back_the_rest_of_the_tax(self):
        services.refund(self.order, self.tea.net_amount, "Stale", items={self.tea: 1})
        services.refund(self.order, services.refundable(self.order), "Sent back")
        self.assertEqual(sum(r.tax_amount for r in self.order.refunds.all()), self.order.tax_amount)
        self.assertEqual(sum(r.taxable_amount for r in self.order.refunds.all()), self.order.taxable_amount)

    def test_unspecified_partial_refund_takes_a_share_of_the_order(self):
        quarter = (self.order.total / 4).quantize(Decimal("0.01"))
        refund = services.refund(self.order, quarter, "Sorry")
        self.assertEqual(refund.tax_amount, checkout_tax.money(quarter * self.order.tax_amount / self.order.total))

    def test_cancelling_gives_back_all_the_tax(self):
        services.cancel_order(self.order, "Customer asked")
        refund = self.order.refunds.get()
        self.assertEqual((refund.taxable_amount, refund.tax_amount),
                         (self.order.taxable_amount, self.order.tax_amount))

    def test_migration_fills_in_earlier_refunds_as_a_share_of_the_order(self):
        quarter = (self.order.total / 4).quantize(Decimal("0.01"))
        first = Refund.objects.create(order=self.order, kind="partial", amount=quarter, reason="old")
        last = Refund.objects.create(order=self.order, kind="partial", amount=self.order.total - quarter,
                                     reason="old", created_at=first.created_at + timedelta(minutes=1))
        importlib.import_module("apps.fulfillment.migrations.0002_refund_tax").fill_in(django_apps, None)
        first.refresh_from_db()
        last.refresh_from_db()
        self.assertEqual(first.tax_amount, checkout_tax.money(quarter * self.order.tax_amount / self.order.total))
        self.assertEqual(first.tax_amount + last.tax_amount, self.order.tax_amount)
        self.assertEqual(first.taxable_amount + last.taxable_amount, self.order.taxable_amount)


class ReshipAndAddressTests(FulfillmentTestCase):
    def test_reship_a_lost_parcel(self):
        order = paid_order([(self.assam, 2)])
        self.pack_all(order)
        self.ship(order)
        order.refresh_from_db()
        line = order.lines.get()
        parcel = services.start_reship(order, {line: 1}, "Lost in the post")
        self.assertEqual(parcel.kind, Parcel.Kind.RESHIP)
        self.pack_all(order)
        label, _ = services.buy_label(parcel, weight_grams=150, service=order.shipping_service,
                                      box=BoxSize.objects.get(item__code="BOX-S"))
        order.refresh_from_db()
        self.assertEqual(order.tracking_number, label.tracking_number)
        self.assertIn("again", mail.outbox[-1].subject)
        self.assertEqual(SoldPackage.objects.filter(order_reference=order.number).count(), 3)

    def test_change_address_checks_it(self):
        order = paid_order([(self.assam, 1)])
        new = Address(name="Ada", street1="5 Elm St", city="Troy", state="NY", zip="12180")
        services.change_address(order, new)
        order.refresh_from_db()
        self.assertEqual((order.ship_street1, order.ship_city), ("5 ELM ST", "TROY"))
        with self.assertRaises(services.FulfillmentError):
            services.change_address(order, Address(name="Ada", street1="1 Main", city="Juneau", state="AK",
                                                   zip="99801"))


class DelayNoticeTests(FulfillmentTestCase):
    def test_short_delay_silence_is_consent(self):
        order = paid_order([(self.assam, 1)], ship_by=date.today() + timedelta(days=1))
        notice = services.send_delay_notice(order, date.today() + timedelta(days=10), "Waiting for the importer")
        order.refresh_from_db()
        notice.refresh_from_db()  # the email job set sent_at
        self.assertFalse(notice.needs_consent)
        self.assertEqual(order.ship_by, notice.new_ship_by)
        self.assertIsNotNone(notice.sent_at)
        self.assertIn("will ship later", mail.outbox[-1].subject)
        self.assertIn(f"/orders/{order.token}/delay/{notice.pk}/", mail.outbox[-1].body)

    def test_long_or_second_delay_needs_consent(self):
        order = paid_order([(self.assam, 1)], ship_by=date.today() + timedelta(days=1))
        notice = services.send_delay_notice(order, date.today() + timedelta(days=45), "A long wait")
        self.assertTrue(notice.needs_consent)
        order.refresh_from_db()
        self.assertEqual(order.ship_by, date.today() + timedelta(days=1))  # not moved until they agree
        services.answer_delay(notice, wait=True)
        order.refresh_from_db()
        self.assertEqual(order.ship_by, notice.new_ship_by)
        second = services.send_delay_notice(order, notice.new_ship_by + timedelta(days=3), "Still waiting")
        self.assertTrue(second.needs_consent)

    def test_customer_cancels_for_a_full_refund(self):
        order = paid_order([(self.assam, 1)])
        notice = services.send_delay_notice(order, date.today() + timedelta(days=12), "Out of stock")
        services.answer_delay(notice, wait=False)
        order.refresh_from_db()
        notice.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(notice.response, DelayNotice.Response.CANCELLED)
        self.assertEqual(services.refundable(order), Decimal("0.00"))

    def test_no_answer_in_time_is_flagged(self):
        order = paid_order([(self.assam, 1)])
        notice = services.send_delay_notice(order, date.today() + timedelta(days=60), "A long wait")
        self.assertEqual(list(services.consent_overdue(notice.answer_by + timedelta(days=1))), [notice])
        self.assertEqual(list(services.consent_overdue(notice.answer_by)), [])


class SummaryTests(FulfillmentTestCase):
    def test_daily_summary_lists_new_and_late_orders_once(self):
        late = paid_order([(self.assam, 1)], ship_by=date.today() - timedelta(days=1))
        new = paid_order([(self.teapot, 1)])
        sent = summary.send()
        self.assertEqual({o.pk for o in sent.new_orders}, {late.pk, new.pk})
        message = mail.outbox[-1]
        self.assertEqual(message.to, ["owner@example.com"])
        self.assertIn("2 new orders, 1 past the promised ship date", message.subject)
        self.assertIn(late.number, message.body)
        new.refresh_from_db()
        self.assertIsNotNone(new.owner_notified_at)
        # Next day: the late one is still late, so it is sent again, but with no new orders.
        again = summary.send()
        self.assertEqual(again.new_orders, [])

    def test_nothing_to_say_sends_nothing(self):
        self.assertIsNone(summary.send())
        self.assertEqual(mail.outbox, [])

    @override_settings(OWNER_NEW_ORDER_EMAILS="each")
    def test_an_email_per_order_when_chosen(self):
        from apps.checkout import emails

        order = paid_order([(self.assam, 1)])
        self.assertTrue(emails.owner_new_order(order))

    def test_default_is_no_email_per_order(self):
        from apps.checkout import emails

        self.assertFalse(emails.owner_new_order(paid_order([(self.assam, 1)])))


class PickupTests(FulfillmentTestCase):
    def test_book_and_cancel_a_pickup(self):
        with self.assertRaisesMessage(services.FulfillmentError, "No labelled parcels"):
            services.schedule_pickup(services.next_pickup_day(), location="Front door")
        order = paid_order([(self.assam, 1)])
        self.pack_all(order)
        label, _ = self.ship(order)
        pickup = services.schedule_pickup(services.next_pickup_day(), location="Front door")
        self.assertTrue(pickup.confirmation)
        label.refresh_from_db()
        self.assertEqual(label.pickup, pickup)
        services.cancel_pickup(pickup)
        label.refresh_from_db()
        self.assertIsNone(label.pickup)
        self.assertEqual(pickup.status, Pickup.Status.CANCELLED)

    def test_no_sunday_pickups(self):
        day = timezone.localdate() + timedelta(days=1)
        while day.weekday() != 6:
            day += timedelta(days=1)
        self.assertNotEqual(services.next_pickup_day(day - timedelta(days=1)).weekday(), 6)


class StripeRefundTests(TestCase):
    def test_refund_goes_to_the_payment_intent(self):
        from apps.checkout.payments import StripePayments

        client = mock.Mock()
        client.v1.refunds.create.return_value = mock.Mock(id="re_123")
        order = mock.Mock(number="261101-ABCD", payment_id="pi_42")
        self.assertEqual(StripePayments(client=client).refund(order, Decimal("12.34"), "k1"), "re_123")
        params = client.v1.refunds.create.call_args.kwargs["params"]
        self.assertEqual((params["payment_intent"], params["amount"]), ("pi_42", 1234))
        self.assertEqual(client.v1.refunds.create.call_args.kwargs["options"], {"idempotency_key": "refund-k1"})
