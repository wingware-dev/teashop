from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalog import alerts, services
from apps.catalog.models import BomLine, Product, SizeOption, SoldPackage
from apps.core.testing import login_verified, make_owner
from apps.inventory import tracing
from apps.inventory.models import Item, Lot, StockMovement
from apps.inventory.services import StockError
from apps.inventory.testing import make_item, make_lot

PACKER = "Teashop\nPO Box 12\nKingston, NY 12401"


def make_tea_product(tea, sizes=((50, "12.00"),), **fields):
    product = Product.objects.create(name=tea.name, slug=tea.code.lower(), tea=tea,
                                     label_name=f"{tea.name} black tea", **fields)
    tin = Item.objects.get_or_create(name="Tin", defaults={"code": "TIN", "kind": Item.Kind.PACKAGING})[0]
    label = Item.objects.get_or_create(name="Label", defaults={"code": "LABEL", "kind": Item.Kind.PACKAGING})[0]
    for grams, price in sizes:
        size = SizeOption.objects.create(product=product, name=f"{grams} g tin", sku=f"{tea.code}-{grams}",
                                         net_grams=grams, price=Decimal(price))
        BomLine.objects.create(size_option=size, item=tin)
        BomLine.objects.create(size_option=size, item=label)
    return product


class ProductValidationTests(TestCase):
    def test_tea_needs_bulk_tea_and_goods_must_not(self):
        with self.assertRaises(ValidationError):
            Product(name="x", slug="x", kind=Product.Kind.TEA).full_clean()
        with self.assertRaises(ValidationError):
            Product(name="x", slug="x", kind=Product.Kind.GOODS, tea=make_item("Assam")).full_clean()

    def test_size_net_grams_rules(self):
        tea = make_tea_product(make_item("Assam"))
        with self.assertRaises(ValidationError):
            SizeOption(product=tea, name="tin", sku="A", price=1).full_clean()
        mug = Product.objects.create(name="Mug", slug="mug", kind=Product.Kind.GOODS)
        with self.assertRaises(ValidationError):
            SizeOption(product=mug, name="mug", sku="M", price=1, net_grams=5).full_clean()

    def test_bom_line_must_be_by_unit(self):
        size = make_tea_product(make_item("Assam")).size_options.get()
        with self.assertRaises(ValidationError):
            BomLine(size_option=size, item=make_item("Ceylon"), quantity=1).full_clean()


class PackTests(TestCase):
    def setUp(self):
        self.assam = make_item("Assam")
        self.product = make_tea_product(self.assam, sizes=((50, "12.00"), (100, "21.00")))
        self.small = self.product.size_options.get(net_grams=50)
        self.tin = Item.objects.get(code="TIN")
        self.label = Item.objects.get(code="LABEL")
        make_lot(self.tin, 10)
        make_lot(self.label, 10)

    def test_bill_of_materials(self):
        self.assertEqual(
            [(item.code, qty) for item, qty in self.small.bill_of_materials()],
            [("ASSAM", 50), ("TIN", 1), ("LABEL", 1)],
        )

    def test_pack_takes_bom_from_stock_fefo(self):
        old = make_lot(self.assam, 1000, best_by=date(2027, 5, 1))
        new = make_lot(self.assam, 1000, best_by=date(2028, 5, 1))
        package = services.pack(self.small, "1001", tea_grams=51)
        self.assertEqual(package.tea_lot, old)
        self.assertEqual(package.tea_grams, 51)
        self.assertEqual(package.amount, Decimal("12.00"))
        self.assertFalse(package.organic)
        old.refresh_from_db()
        new.refresh_from_db()
        self.assertEqual((old.quantity_on_hand, new.quantity_on_hand), (949, 1000))
        self.assertEqual(self.tin.on_hand(), 9)
        self.assertEqual(self.label.on_hand(), 9)
        self.assertEqual(StockMovement.objects.filter(reference="1001", kind=StockMovement.Kind.SALE).count(), 3)
        self.assertEqual(tracing.trace(old).order_references(), ["1001"])

    def test_pack_under_net_weight_refused(self):
        make_lot(self.assam, 1000)
        with self.assertRaises(StockError):
            services.pack(self.small, "1001", tea_grams=49)

    def test_pack_short_packaging_takes_nothing(self):
        lot = make_lot(self.assam, 1000)
        self.label.lots.update(status=Lot.Status.ON_HOLD)
        with self.assertRaises(StockError):
            services.pack(self.small, "1001")
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_on_hand, 1000)
        self.assertEqual(self.tin.on_hand(), 10)
        self.assertFalse(SoldPackage.objects.exists())

    def test_pack_from_chosen_lot(self):
        make_lot(self.assam, 1000, best_by=date(2027, 1, 1))
        chosen = make_lot(self.assam, 1000, best_by=date(2028, 1, 1))
        self.assertEqual(services.pack(self.small, "1001", lot=chosen).tea_lot, chosen)
        with self.assertRaises(StockError):
            services.pack(self.small, "1002", lot=make_lot(make_item("Ceylon"), 100))

    def test_packages_available(self):
        make_lot(self.assam, 120)
        make_lot(self.assam, 90)
        # 2 + 1 whole packages of 50 g; the tins (10) are not the limit.
        self.assertEqual(self.small.packages_available(), 3)
        self.assertEqual(self.product.size_options.get(net_grams=100).packages_available(), 1)

    def test_goods_product(self):
        mug_item = make_item("Mug", code="MUG", kind=Item.Kind.MERCH)
        make_lot(mug_item, 3)
        mug = Product.objects.create(name="Mug", slug="mug", kind=Product.Kind.GOODS)
        size = SizeOption.objects.create(product=mug, name="Mug", sku="MUG", price=Decimal("18"))
        BomLine.objects.create(size_option=size, item=mug_item)
        package = services.pack(size, "1001", amount="15.00")
        self.assertIsNone(package.tea_lot)
        self.assertEqual(package.amount, Decimal("15.00"))
        self.assertEqual(mug_item.on_hand(), 2)
        self.assertEqual(size.packages_available(), 2)
        with self.assertRaises(ValueError):
            services.label_data(size, None)


class OrganicTests(TestCase):
    def setUp(self):
        self.sencha = make_item("Sencha")
        self.product = make_tea_product(self.sencha, sizes=((50, "1000.00"),), sold_as_organic=True)
        self.size = self.product.size_options.get()
        make_lot(Item.objects.get(code="TIN"), 10)
        make_lot(Item.objects.get(code="LABEL"), 10)

    def test_only_organic_lots_packed(self):
        make_lot(self.sencha, 1000, best_by=date(2027, 1, 1), organic=False)
        organic = make_lot(self.sencha, 1000, best_by=date(2028, 1, 1), organic=True)
        package = services.pack(self.size, "1001")
        self.assertEqual(package.tea_lot, organic)
        self.assertTrue(package.organic)
        with self.assertRaises(StockError):
            services.pack(self.size, "1002", lot=self.sencha.lots.get(organic=False))

    @override_settings(ORGANIC_SALES_ALERT=4000, ORGANIC_EXEMPTION_LIMIT=5000)
    def test_threshold_alerts(self):
        make_lot(self.sencha, 1000, organic=True)
        for n in range(3):
            services.pack(self.size, f"10{n}")
        self.assertEqual(services.organic_sales(), Decimal("3000.00"))
        self.assertIsNone(alerts.organic_alert())
        services.pack(self.size, "104")
        alert = alerts.organic_alert()
        self.assertEqual((alert.level, alert.title), ("warning", "Organic sales this year: $4,000.00 of the $5,000 limit"))
        services.pack(self.size, "105")
        self.assertEqual(alerts.organic_alert().level, "urgent")
        self.assertEqual(services.organic_sales(year=2001), Decimal("0.00"))


@override_settings(LABEL_PACKER_ADDRESS=PACKER)
class LabelTests(TestCase):
    def setUp(self):
        self.assam = make_item("Assam")
        self.size = make_tea_product(self.assam).size_options.get()

    def test_ounces_round_down(self):
        self.assertEqual(services.ounces(50), Decimal("1.76"))
        self.assertEqual(services.ounces(100), Decimal("3.52"))
        self.assertEqual(services.net_weight_text(25), "Net wt 0.88 oz (25 g)")

    def test_label_from_lot(self):
        lot = make_lot(self.assam, 1000, best_by=date(2028, 1, 1), country="India, Sri Lanka", allergens=["milk", "tree-nuts"])
        label = services.label_data(self.size, lot)
        self.assertEqual(label.name, "Assam black tea")
        self.assertEqual(label.net_weight, "Net wt 1.76 oz (50 g)")
        self.assertEqual(label.grown_in, "Grown in India and Sri Lanka")
        self.assertEqual(label.ingredients, "black tea")
        self.assertEqual(label.contains, "Contains: Milk and Tree nuts")
        self.assertEqual(label.lot_code, lot.code)
        self.assertEqual(label.best_by, date(2028, 1, 1))
        self.assertEqual(label.packer, PACKER)
        self.assertEqual(label.problems, [])

    @override_settings(LABEL_PACKER_ADDRESS="")
    def test_label_problems(self):
        lot = Lot.objects.create(item=self.assam, quantity_received=100)
        problems = services.label_data(self.size, lot).problems
        self.assertEqual(len(problems), 3, problems)


class CatalogAdminTests(TestCase):
    def setUp(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)

    def test_pages_render(self):
        assam = make_item("Assam")
        product = make_tea_product(assam)
        size = product.size_options.get()
        make_lot(Item.objects.get(code="TIN"), 5)
        make_lot(Item.objects.get(code="LABEL"), 5)
        make_lot(assam, 500)
        package = services.pack(size, "1001")
        pages = [
            reverse("admin:catalog_product_changelist"),
            reverse("admin:catalog_product_add"),
            reverse("admin:catalog_product_change", args=[product.pk]),
            reverse("admin:catalog_sizeoption_changelist"),
            reverse("admin:catalog_sizeoption_change", args=[size.pk]),
            reverse("admin:catalog_soldpackage_changelist"),
            reverse("admin:catalog_soldpackage_change", args=[package.pk]),
        ]
        for page in pages:
            with self.subTest(page=page):
                self.assertEqual(self.client.get(page).status_code, 200)
        response = self.client.get(reverse("admin:catalog_sizeoption_change", args=[size.pk]))
        self.assertContains(response, "50 g Assam")
        self.assertContains(response, "Net wt 1.76 oz (50 g)")
        response = self.client.get(reverse("admin:catalog_soldpackage_change", args=[package.pk]))
        self.assertContains(response, "Grown in India")
        self.assertContains(response, "Organic sales this year", count=0)
        self.assertContains(self.client.get(reverse("admin:catalog_soldpackage_changelist")), "Organic sales this year: $0.00")

    def test_dashboard_lists_unpackable_sizes(self):
        make_tea_product(make_item("Assam"))
        response = self.client.get(reverse("core:owner_dashboard"))
        self.assertContains(response, "Can&#x27;t be packed from stock: 1 size")
