"""Package labels as PDF, and EasyPost's label and pickup calls (with a
stand-in HTTP session: no network, no postage)."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase, override_settings

from apps.catalog.services import Label
from apps.fulfillment import carriers, labels, pdf
from apps.fulfillment.testing import PACKER


def make_label(**changes):
    facts = dict(name="Assam black tea", net_weight="Net wt 1.76 oz (50 g)", grown_in="Grown in India",
                 ingredients="black tea", allergens=[], lot_code="ASSAM-261101", best_by=date(2028, 1, 1),
                 packer=PACKER)
    facts.update(changes)
    return Label(**facts)


class PdfTests(SimpleTestCase):
    def test_a_well_formed_pdf(self):
        doc = pdf.Document(288, 144, title="Test")
        doc.page().text(10, 100, "Grown in India (Assam)", size=9)
        data = doc.render()
        self.assertTrue(data.startswith(b"%PDF-1.4"))
        self.assertTrue(data.rstrip().endswith(b"%%EOF"))
        self.assertIn(b"(Grown in India \\(Assam\\)) Tj", data)
        # The cross-reference offsets point at the objects.
        xref = int(data.rsplit(b"startxref\n", 1)[1].split(b"\n")[0])
        self.assertTrue(data[xref:].startswith(b"xref"))
        first = int(data[xref:].split(b"\n")[3].split()[0])
        self.assertTrue(data[first:].startswith(b"1 0 obj"))

    def test_wrap(self):
        lines = pdf.wrap("Ingredients: black tea, almond pieces, natural vanilla flavour", 100, 9)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(pdf.text_width(line, 9) <= 100 for line in lines))


class PackageLabelTests(SimpleTestCase):
    def test_net_weight_type_size_follows_the_label_area(self):
        # 8 square inches: letters at least 1/8 inch, lower-case "o" included.
        self.assertGreaterEqual(labels.net_weight_size(4, 2) * labels.X_HEIGHT, 72 / 8)
        self.assertGreaterEqual(labels.net_weight_size(2, 1) * labels.X_HEIGHT, 72 / 16)

    def test_label_has_every_fact(self):
        page = pdf.Page(288, 144)
        labels.draw_package_label(page, make_label(allergens=["Tree nuts"]), 4, 2)
        content = page.content()
        for text in (b"Assam black tea", b"Net wt 1.76 oz \\(50 g\\)", b"Grown in India", b"Ingredients: black tea",
                     b"Contains: Tree nuts", b"Lot ASSAM-261101", b"Best by 01/01/2028",
                     b"Packed by Teashop LLC, 1 Main St, Albany, NY 12207"):
            self.assertIn(text, content)

    def test_too_much_for_a_tiny_label(self):
        with self.assertRaises(labels.LabelError):
            labels.draw_package_label(pdf.Page(72, 36), make_label(ingredients="black tea, " * 30), 1, 0.5)

    def test_label_size_setting(self):
        self.assertEqual(labels.label_size("3 x 2"), (3.0, 2.0))
        with self.assertRaises(labels.LabelError):
            labels.label_size("big")


class FakeResponse:
    def __init__(self, status, data=None, content=b""):
        self.status_code = status
        self._data = data
        self.content = content
        self.text = str(data)

    def json(self):
        if self._data is None:
            raise ValueError("not JSON")
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def request(self, method, url, json=None, auth=None, timeout=None):
        self.calls.append((method, url, json))
        return self.answers.pop(0)

    def get(self, url, timeout=None):
        self.calls.append(("GET", url, None))
        return self.answers.pop(0)


ORDER = SimpleNamespace(number="261101-ABCD",
                        address=SimpleNamespace(as_dict=lambda: {"name": "Ada", "street1": "12 Main St", "street2": "",
                                                                 "city": "Albany", "state": "NY", "zip": "12207"}))
RATES = [{"id": "rate_ga", "carrier": "USPS", "service": "GroundAdvantage", "rate": "5.10"},
         {"id": "rate_pm", "carrier": "USPS", "service": "Priority", "rate": "9.20"}]


@override_settings(SHIP_FROM={"name": "Teashop", "street1": "1 Main St", "street2": "", "city": "Albany",
                              "state": "NY", "zip": "12207", "phone": ""})
class EasyPostTests(SimpleTestCase):
    def test_buy_the_service_the_customer_chose(self):
        session = FakeSession([
            FakeResponse(201, {"id": "shp_1", "rates": RATES}),
            FakeResponse(200, {"id": "shp_1", "tracking_code": "9400111", "selected_rate": RATES[1],
                               "postage_label": {"label_pdf_url": "https://labels.example/1.pdf"}}),
            FakeResponse(200, content=b"%PDF-label"),
        ])
        provider = carriers.EasyPostLabels("EZTKtest", session=session)
        bought = provider.buy(ORDER, weight_grams=340, dimensions=[Decimal(7), Decimal(5), Decimal(5)],
                              service="USPS Priority Mail", label_format="PDF")
        self.assertEqual((bought.tracking_number, bought.postage, bought.label), ("9400111", Decimal("9.20"),
                                                                                b"%PDF-label"))
        self.assertTrue(bought.test_mode)
        shipment = session.calls[0][2]["shipment"]
        self.assertEqual(shipment["parcel"], {"weight": 12.0, "length": 7.0, "width": 5.0, "height": 5.0})
        self.assertEqual(shipment["options"]["label_size"], "4x6")
        self.assertEqual(session.calls[1][2], {"rate": {"id": "rate_pm"}})

    def test_service_not_offered(self):
        session = FakeSession([FakeResponse(201, {"id": "shp_1", "rates": RATES[:1]})])
        with self.assertRaisesMessage(carriers.CarrierError, "does not offer USPS Priority Mail"):
            carriers.EasyPostLabels("EZTKtest", session=session).buy(
                ORDER, weight_grams=100, dimensions=None, service="USPS Priority Mail", label_format="PDF")

    def test_refusal_is_reported(self):
        session = FakeSession([FakeResponse(422, {"error": {"message": "Invalid address"}})])
        with self.assertRaisesMessage(carriers.CarrierError, "Invalid address"):
            carriers.EasyPostLabels("EZTKtest", session=session).buy(
                ORDER, weight_grams=100, dimensions=None, service="USPS Ground Advantage", label_format="PDF")

    def test_pickup(self):
        session = FakeSession([
            FakeResponse(201, {"id": "pickup_1", "pickup_rates": [{"carrier": "USPS", "service": "NextDay"}]}),
            FakeResponse(200, {"id": "pickup_1", "confirmation": "WTC123"}),
        ])
        booked = carriers.EasyPostLabels("EZTKtest", session=session).schedule_pickup(
            date(2026, 11, 3), shipment_id="shp_1", location="Front door", instructions="", reference="r")
        self.assertEqual(booked.confirmation, "WTC123")
        self.assertEqual(session.calls[1][2], {"carrier": "USPS", "service": "NextDay"})

    @override_settings(SHIPPING_PROVIDER="easypost", EASYPOST_API_KEY="EZAKlive", EASYPOST_ALLOW_LIVE=False)
    def test_live_key_refused_without_allow_live(self):
        from django.core.exceptions import ImproperlyConfigured

        with self.assertRaises(ImproperlyConfigured):
            carriers.provider()


class ReversePackageTests(TestCase):
    """catalog.services.reverse_package: the opposite of pack()."""

    def setUp(self):
        from apps.catalog.models import BomLine, Product, SizeOption
        from apps.inventory.testing import make_item, make_lot

        self.tea = make_item("Assam")
        self.tin = make_item("Tin", code="TIN", kind="packaging")
        self.tea_lot = make_lot(self.tea, 1000)
        self.tin_lots = [make_lot(self.tin, 1), make_lot(self.tin, 5)]
        product = Product.objects.create(name="Assam", slug="assam", tea=self.tea, label_name="Assam black tea",
                                         sold_as_organic=False)
        self.size = SizeOption.objects.create(product=product, name="50 g tin", sku="A-50", net_grams=50,
                                              price=Decimal("9"))
        BomLine.objects.create(size_option=self.size, item=self.tin)

    def test_everything_goes_back_where_it_came_from(self):
        from apps.catalog import services as catalog
        from apps.inventory.models import StockMovement

        first = catalog.pack(self.size, "ORDER-1", tea_grams=51)
        second = catalog.pack(self.size, "ORDER-1", tea_grams=50)
        catalog.reverse_package(second, "Customer cancelled")
        catalog.reverse_package(first, "Customer cancelled")
        for lot in [self.tea_lot, *self.tin_lots]:
            lot.refresh_from_db()
            self.assertEqual(lot.quantity_on_hand, lot.quantity_received)
        returned = StockMovement.objects.filter(reason=StockMovement.Reason.RETURNED, reference="ORDER-1")
        self.assertEqual(returned.count(), 4)
        with self.assertRaises(ValueError):
            catalog.reverse_package(first)
        self.assertEqual(catalog.organic_sales(), Decimal("0.00"))

    def test_not_reusable_is_written_off(self):
        from apps.catalog import services as catalog
        from apps.inventory.models import StockMovement

        package = catalog.pack(self.size, "ORDER-2", tea_grams=50)
        catalog.reverse_package(package, "Spilled", reusable=False)
        self.tea_lot.refresh_from_db()
        self.assertEqual(self.tea_lot.quantity_on_hand, 950)
        self.assertTrue(StockMovement.objects.filter(reason=StockMovement.Reason.DAMAGED, reference="ORDER-2",
                                                     quantity=-50).exists())

    def test_reversed_packages_leave_the_profit_report(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.catalog import services as catalog
        from apps.purchasing import reports

        package = catalog.pack(self.size, "ORDER-3", tea_grams=50)
        today = timezone.localdate()
        self.assertEqual(reports.profitability(today, today + timedelta(days=1))[2].packages, 1)
        catalog.reverse_package(package)
        self.assertEqual(reports.profitability(today, today + timedelta(days=1))[2].packages, 0)
