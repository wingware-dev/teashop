"""The fulfillment pages through the test client: the owner packs, labels
and ships; the customer answers a delay notice."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.checkout.models import Order
from apps.core.testing import login_verified, make_owner
from apps.fulfillment import services
from apps.fulfillment.models import BoxSize, PackedPackage
from apps.fulfillment.testing import paid_order, size

from .test_services import FulfillmentTestCase


class OwnerPagesTests(FulfillmentTestCase):
    def setUp(self):
        super().setUp()
        owner, device = make_owner()
        login_verified(self.client, owner, device)

    def test_pages_need_the_owner(self):
        self.client.logout()
        response = self.client.get(reverse("fulfillment:queue"))
        self.assertEqual(response.status_code, 302)

    def test_queue_lists_orders_soonest_first_allergens_last(self):
        late = paid_order([(self.assam, 1)], ship_by=date.today() - timedelta(days=1))
        allergen = paid_order([(self.vanilla, 1)], ship_by=date.today() + timedelta(days=2))
        plain = paid_order([(self.assam, 1)], ship_by=date.today() + timedelta(days=2))
        page = self.client.get(reverse("fulfillment:queue"))
        self.assertEqual([row["order"] for row in page.context["rows"]], [late, plain, allergen])
        self.assertContains(page, "past the promised ship date")
        self.assertContains(page, "Contains Tree nuts: pack last")

    def test_back_ordered_orders_have_their_own_tab(self):
        waiting = paid_order([(self.assam, 1)])
        services.backorder(services.parcels(waiting)[0], date.today() + timedelta(days=5), "Restocking")
        to_pack = self.client.get(reverse("fulfillment:queue"))
        self.assertNotIn(waiting, [row["order"] for row in to_pack.context["rows"]])
        backordered = self.client.get(reverse("fulfillment:queue") + "?show=backordered")
        self.assertEqual([row["order"] for row in backordered.context["rows"]], [waiting])

    def test_shipped_tab_judges_lateness_by_the_ship_date(self):
        # Shipped at noon local time on calendar days, as the view judges by
        # local dates (24 hours back is not always yesterday: DST).
        today = timezone.localdate()

        def noon(days_ago):
            return timezone.make_aware(datetime.combine(today - timedelta(days=days_ago), time(12)))

        on_time = paid_order([(self.assam, 1)], ship_by=today - timedelta(days=3))
        late = paid_order([(self.assam, 1)], ship_by=today - timedelta(days=3))
        Order.objects.filter(pk=on_time.pk).update(status=Order.Status.SHIPPED, shipped_at=noon(4))
        Order.objects.filter(pk=late.pk).update(status=Order.Status.SHIPPED, shipped_at=noon(1))
        page = self.client.get(reverse("fulfillment:queue") + "?show=shipped")
        rows = {row["order"]: row for row in page.context["rows"]}
        self.assertEqual((rows[on_time]["status"], rows[on_time]["status_text"]), ("ok", ""))
        self.assertEqual(rows[late]["status"], "late")
        self.assertTrue(rows[late]["status_text"].startswith("Shipped late: promised"))
        self.assertIn("(2 days after)", rows[late]["status_text"])
        self.assertNotContains(page, "Late: promised")

    def test_packing_list_puts_allergen_teas_last(self):
        paid_order([(self.vanilla, 2), (self.assam, 3)])
        page = self.client.get(reverse("fulfillment:packing_list"))
        self.assertEqual([g["count"] for g in page.context["plain"]], [3])
        self.assertEqual([g["count"] for g in page.context["allergen"]], [2])
        self.assertContains(page, "Pack last: allergen teas")

    def test_pack_print_and_ship_through_the_pages(self):
        order = paid_order([(self.assam, 1)])
        page = self.client.get(reverse("fulfillment:order", args=[order.number]))
        self.assertContains(page, "Pack and print label")
        parcel = services.parcels(order)[0]
        line = order.lines.get()
        prefix = f"p{parcel.pk}-l{line.pk}"
        response = self.client.post(reverse("fulfillment:pack", args=[parcel.pk, line.pk]), {
            f"{prefix}-measured_grams": "50.2", f"{prefix}-scale": self.scale.pk})
        packed = PackedPackage.objects.get()
        self.assertRedirects(response, reverse("fulfillment:order", args=[order.number]) + f"?print={packed.pk}#print",
                             fetch_redirect_response=False)
        page = self.client.get(response.url)
        self.assertContains(page, "Print the package label")
        pdf = self.client.get(reverse("fulfillment:package_labels", args=[parcel.pk]) + f"?packages={packed.pk}")
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        packed.refresh_from_db()
        self.assertIsNotNone(packed.label_printed_at)

        small = BoxSize.objects.get(item__code="BOX-S")
        response = self.client.post(reverse("fulfillment:buy_label", args=[parcel.pk]), {
            f"label{parcel.pk}-box": small.pk, f"label{parcel.pk}-weight": "5.5", f"label{parcel.pk}-unit": "oz",
            f"label{parcel.pk}-service": "USPS Ground Advantage"}, follow=True)
        self.assertContains(response, "Label bought")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        label = parcel.labels.get()
        self.assertEqual(label.weight_grams, 156)
        file = self.client.get(reverse("fulfillment:shipping_label", args=[label.pk]))
        self.assertEqual(file["Content-Type"], "application/pdf")
        self.assertTrue(b"".join(file.streaming_content).startswith(b"%PDF"))

    def test_allergen_warning_and_refusal_without_confirmation(self):
        order = paid_order([(self.vanilla, 1)])
        page = self.client.get(reverse("fulfillment:order", args=[order.number]))
        self.assertContains(page, "Allergens: contains Tree nuts")
        parcel = services.parcels(order)[0]
        line = order.lines.get()
        prefix = f"p{parcel.pk}-l{line.pk}"
        response = self.client.post(reverse("fulfillment:pack", args=[parcel.pk, line.pk]), {
            f"{prefix}-measured_grams": "50", f"{prefix}-scale": self.scale.pk}, follow=True)
        self.assertContains(response, "Confirm the allergen handling")
        self.assertFalse(PackedPackage.objects.exists())

    def test_cancel_refund_and_delay_forms(self):
        order = paid_order([(self.assam, 1)])
        url = reverse("fulfillment:order", args=[order.number])
        self.client.post(reverse("fulfillment:delay_notice", args=[order.number]), {
            "delay-new_ship_by": (date.today() + timedelta(days=9)).isoformat(), "delay-reason": "Restocking"})
        self.assertTrue(order.delay_notices.exists())
        self.client.post(reverse("fulfillment:refund", args=[order.number]), {
            "refund-amount": "2.00", "refund-reason": "Late"})
        self.assertEqual(services.refunded(order), Decimal("2.00"))
        response = self.client.post(reverse("fulfillment:cancel", args=[order.number]), {
            "cancel-reason": "Customer asked", "cancel-reusable": "on"}, follow=True)
        self.assertRedirects(response, url)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(services.refunded(order), order.total)

    def test_refund_form_says_what_the_refund_is_for(self):
        order = paid_order([(self.assam, 1), (size("glass-teapot"), 1)])
        Order.objects.filter(pk=order.pk).update(taxable_amount=Decimal("28.00"), tax_amount=Decimal("2.24"),
                                                 total=order.total + Decimal("2.24"))
        order.refresh_from_db()
        tea = order.lines.get(taxable=False)
        url = reverse("fulfillment:order", args=[order.number])
        page = self.client.get(url)
        self.assertContains(page, "What it is for")
        self.assertContains(page, f'name="refund-line_{tea.pk}"')
        self.assertContains(page, 'name="refund-shipping"')
        response = self.client.post(reverse("fulfillment:refund", args=[order.number]), {
            "refund-amount": str(tea.net_amount), "refund-reason": "Stale", f"refund-line_{tea.pk}": "1"},
            follow=True)
        refund = order.refunds.get()
        self.assertEqual((refund.amount, refund.tax_amount), (tea.net_amount, Decimal("0.00")))
        response = self.client.post(reverse("fulfillment:refund", args=[order.number]), {
            "refund-amount": "30.25", "refund-reason": "Broken", f"refund-line_{order.lines.get(taxable=True).pk}": "1"},
            follow=True)
        self.assertContains(response, "more than what you ticked")
        self.assertEqual(order.refunds.count(), 1)
        response = self.client.post(reverse("fulfillment:refund", args=[order.number]), {
            "refund-amount": "30.24", "refund-reason": "Broken", f"refund-line_{order.lines.get(taxable=True).pk}": "1"},
            follow=True)
        self.assertContains(response, "(with $2.24 tax)")

    def test_address_reship_and_pickup_pages(self):
        order = paid_order([(self.assam, 1)])
        response = self.client.post(reverse("fulfillment:address", args=[order.number]), {
            "name": "Ada Lovelace", "street1": "5 Elm St", "city": "Troy", "state": "NY", "zip": "12180"})
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.ship_city, "TROY")
        self.pack_all(order)
        self.ship(order)
        self.assertEqual(self.client.get(reverse("fulfillment:reship", args=[order.number])).status_code, 200)
        page = self.client.get(reverse("fulfillment:pickups"))
        self.assertContains(page, "Parcels waiting for a pickup: 1")
        response = self.client.post(reverse("fulfillment:pickups"), {
            "day": services.next_pickup_day().isoformat(), "location": "Porch"}, follow=True)
        self.assertContains(response, "USPS pickup booked")

    def test_installable_app(self):
        self.client.logout()
        manifest = self.client.get(reverse("fulfillment:manifest"))
        self.assertEqual(manifest["Content-Type"], "application/manifest+json")
        self.assertEqual(manifest.json()["start_url"], reverse("fulfillment:queue"))
        worker = self.client.get(reverse("fulfillment:service_worker"))
        self.assertEqual(worker["Service-Worker-Allowed"], reverse("fulfillment:queue"))
        self.assertContains(worker, reverse("fulfillment:offline"))
        self.assertEqual(self.client.get(reverse("fulfillment:offline")).status_code, 200)


@override_settings(STOREFRONT_OPEN=True)
class DelayAnswerPageTests(FulfillmentTestCase):
    def test_customer_cancels_from_the_link(self):
        order = paid_order([(self.assam, 1)])
        notice = services.send_delay_notice(order, date.today() + timedelta(days=50), "A long wait")
        url = reverse("fulfillment:delay_answer", args=[order.token, notice.pk])
        page = self.client.get(url)
        self.assertContains(page, "we will cancel the order and refund you in full")
        response = self.client.post(url, {"choice": "cancel"}, follow=True)
        self.assertContains(response, "Your order is cancelled, as you asked")
        self.assertIn("is cancelled", mail.outbox[-1].subject)

    def test_wrong_token(self):
        order = paid_order([(self.assam, 1)])
        notice = services.send_delay_notice(order, date.today() + timedelta(days=5), "Short")
        self.assertEqual(self.client.get(reverse("fulfillment:delay_answer", args=["nope", notice.pk])).status_code,
                         404)
