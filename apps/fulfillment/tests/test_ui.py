"""The packing pages in a real browser: phone and desktop, light and dark,
WCAG 2.2 AA checks, screenshots (see apps.core.uitesting).  The flow test
packs an allergen tea and a plain one at phone size, prints, and buys the
label, as the owner does at the bench."""

from datetime import timedelta
from decimal import Decimal

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.uitesting import BrowserTestCase
from apps.fulfillment import services
from apps.fulfillment.models import BoxSize, Parcel
from apps.fulfillment.testing import TEST_SETTINGS, paid_order, shop, size


def sample_orders():
    scale = shop()
    assam, vanilla, teapot = size("assam-second-flush"), size("vanilla-almond-black"), size("glass-teapot")
    earl_grey = size("earl-grey-cornflower", 100)
    late = paid_order([(assam, 2), (teapot, 1)], name="Grace Hopper", ship_by=timezone.localdate() - timedelta(days=1))
    allergen = paid_order([(vanilla, 1), (earl_grey, 1)], name="Ada Lovelace", ship_by=timezone.localdate())
    paid_order([(earl_grey, 2)], name="Katherine Johnson", email="kj@example.com",
               ship_by=timezone.localdate() + timedelta(days=3), service="USPS Priority Mail")
    backordered = paid_order([(assam, 1)], name="Dorothy Vaughan", ship_by=timezone.localdate() + timedelta(days=2))
    services.backorder(services.parcels(backordered)[0], timezone.localdate() + timedelta(days=6), "Assam on its way")
    shipped = paid_order([(assam, 1)], name="Mary Jackson", ship_by=timezone.localdate() + timedelta(days=1))
    parcel = services.parcels(shipped)[0]
    services.pack_package(parcel, shipped.lines.get(), measured_grams=Decimal("50.4"), scale=scale)
    services.buy_label(parcel, weight_grams=160, service=shipped.shipping_service,
                       box=BoxSize.objects.get(item__code="BOX-S"))
    return {"late": late, "allergen": allergen, "shipped": shipped, "scale": scale, "backordered": backordered}


@override_settings(**TEST_SETTINGS)
class FulfillmentUITests(BrowserTestCase):
    def test_queue(self):
        sample_orders()
        self.check_page(reverse("fulfillment:queue"), "fulfillment-queue", signed_in=True)

    def test_packing_list(self):
        sample_orders()
        self.check_page(reverse("fulfillment:packing_list"), "fulfillment-packing-list", signed_in=True)

    def test_order_to_pack(self):
        orders = sample_orders()
        self.check_page(reverse("fulfillment:order", args=[orders["allergen"].number]), "fulfillment-order-allergen",
                        signed_in=True)

    def test_order_late(self):
        orders = sample_orders()
        self.check_page(reverse("fulfillment:order", args=[orders["late"].number]), "fulfillment-order-late",
                        signed_in=True)

    def test_order_shipped(self):
        orders = sample_orders()
        self.check_page(reverse("fulfillment:order", args=[orders["shipped"].number]), "fulfillment-order-shipped",
                        signed_in=True)

    def test_pickups_address_reship(self):
        orders = sample_orders()
        self.check_page(reverse("fulfillment:pickups"), "fulfillment-pickups", signed_in=True)
        self.check_page(reverse("fulfillment:address", args=[orders["late"].number]), "fulfillment-address",
                        signed_in=True)
        self.check_page(reverse("fulfillment:reship", args=[orders["shipped"].number]), "fulfillment-reship",
                        signed_in=True)

    def test_customer_delay_answer(self):
        orders = sample_orders()
        notice = services.send_delay_notice(orders["late"], timezone.localdate() + timedelta(days=40),
                                            "Our Assam is on its way from the importer.")
        self.check_page(reverse("fulfillment:delay_answer", args=[orders["late"].token, notice.pk]),
                        "fulfillment-delay-answer")

    def test_pack_and_ship_on_a_phone(self):
        orders = sample_orders()
        order = orders["allergen"]
        page = self.new_page("phone", "light", signed_in=True)
        page.goto(self.url(reverse("fulfillment:queue")))
        page.get_by_role("link", name=order.number).click()
        page.wait_for_load_state()
        # The plain tea first; the allergen tea waits for confirmation.
        forms = page.locator("form.ff-pack-form")
        plain = forms.filter(has_text="Earl Grey")
        plain.get_by_label("Net weight on the scale (g)").fill("100.6")
        plain.get_by_role("button", name="Pack and print label").click()
        page.get_by_role("link", name="Print label").wait_for()
        self.check_current(page, "fulfillment-flow-1-packed")

        allergen = page.locator("form.ff-pack-form").filter(has_text="Vanilla")
        allergen.get_by_label("Net weight on the scale (g)").fill("50.1")
        allergen.get_by_role("button", name="Pack and print label").click()
        page.get_by_text("Confirm the allergen handling").first.wait_for()
        self.check_current(page, "fulfillment-flow-1b-allergen-refused")
        allergen = page.locator("form.ff-pack-form").filter(has_text="Vanilla")
        allergen.get_by_label("Net weight on the scale (g)").fill("50.1")
        allergen.get_by_label("Allergen handling done").check()
        allergen.get_by_role("button", name="Pack and print label").click()
        page.get_by_text("Packed Vanilla Almond Black").wait_for()

        # The browser shows (here: downloads) the PDF; fetch it with the same sign-in.
        labels = page.request.get(self.url(reverse("fulfillment:package_labels",
                                                   args=[services.parcels(order)[0].pk])))
        self.assertEqual(labels.headers["content-type"], "application/pdf")
        self.assertTrue(labels.body().startswith(b"%PDF"))
        self.assertIn(b"Contains: Tree nuts", labels.body())
        page.goto(self.url(reverse("fulfillment:order", args=[order.number])))
        form = page.locator("form.ff-label-form")
        form.get_by_label("Parcel weight").fill("12")
        form.get_by_label("Unit").select_option("oz")
        self.check_current(page, "fulfillment-flow-2-ready-to-label")
        form.get_by_role("button", name="Buy label and ship").click()
        page.get_by_text("Label bought").wait_for()
        self.check_current(page, "fulfillment-flow-3-shipped")
        order.refresh_from_db()
        self.assertEqual(order.status, "shipped")
        self.assertEqual(Parcel.objects.get(order=order).status, Parcel.Status.SHIPPED)
