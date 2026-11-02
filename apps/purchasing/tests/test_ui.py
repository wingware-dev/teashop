"""The purchasing pages in a real browser: phone and desktop, light and
dark, WCAG 2.2 AA checks, screenshots (see apps.core.uitesting)."""

from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from apps.catalog import services as catalog
from apps.catalog.models import BomLine, Product, SizeOption
from apps.core.uitesting import BrowserTestCase
from apps.inventory import services as inventory
from apps.inventory.models import Item, StockMovement
from apps.inventory.testing import make_item, make_lot, make_supplier


def sample_stock():
    supplier = make_supplier()
    supplier.lead_time_days = 21
    supplier.save()
    assam = make_item("Assam", default_supplier=supplier, reorder_level=500)
    sencha = make_item("Sencha", default_supplier=supplier)
    tin = make_item("Tin 100 ml", code="TIN", kind=Item.Kind.PACKAGING, reorder_level=20)
    make_item("Gift box", code="GIFTBOX", kind=Item.Kind.PACKAGING, reorder_level=5)
    old = timezone.localdate() - timedelta(days=120)
    assam_lot = make_lot(assam, 3000, landed_cost=Decimal("42.00"), tariff_cost=Decimal("0"), received_on=old)
    make_lot(sencha, 2000, landed_cost=Decimal("85.00"), tariff_cost=Decimal("12.75"), country="Japan", received_on=old)
    make_lot(tin, 40, landed_cost=Decimal("1.60"), received_on=old)
    product = Product.objects.create(name="Assam", slug="assam", tea=assam, label_name="Assam black tea")
    size = SizeOption.objects.create(product=product, name="100 g tin", sku="ASSAM-100", net_grams=100, price=Decimal("16"))
    BomLine.objects.create(size_option=size, item=tin)
    for n in range(12):
        catalog.pack(size, f"10{n:02d}", tea_grams=101)
    inventory.adjust(assam_lot, -60, StockMovement.Reason.SPOILED, "Damp")
    inventory.adjust(assam_lot, -40, StockMovement.Reason.SAMPLE, "Tea fair")


class PurchasingUITests(BrowserTestCase):
    def test_reorder(self):
        sample_stock()
        self.check_page(reverse("purchasing:reorder"), "purchasing-reorder", signed_in=True)

    def test_losses(self):
        sample_stock()
        self.check_page(reverse("purchasing:losses"), "purchasing-losses", signed_in=True)

    def test_profit(self):
        sample_stock()
        self.check_page(reverse("purchasing:profit"), "purchasing-profit", signed_in=True)
