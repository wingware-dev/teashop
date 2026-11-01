import shutil
import tempfile
from datetime import date

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.testing import login_verified, make_owner
from apps.inventory.models import (
    Allergen,
    BlendBatch,
    Item,
    Lot,
    LotDocument,
    PurchaseOrder,
    PurchaseOrderLine,
    Receipt,
    StockMovement,
)
from apps.inventory.testing import make_item, make_lot, make_recipe, make_supplier

PRIVATE_ROOT = tempfile.mkdtemp(prefix="teashop-private-test-")


def inline_management(prefix, total=0, initial=0):
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": str(initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


@override_settings(PRIVATE_MEDIA_ROOT=PRIVATE_ROOT)
class InventoryAdminTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PRIVATE_ROOT, ignore_errors=True)

    def setUp(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        self.supplier = make_supplier()
        self.assam = make_item("Assam", reorder_level=500)
        self.tin = make_item("Tin 100", code="TIN100", kind=Item.Kind.PACKAGING)

    def test_every_page_renders(self):
        lot = make_lot(self.assam, 1000)
        LotDocument.objects.create(lot=lot, kind=LotDocument.Kind.SPEC_SHEET, file=ContentFile(b"%PDF-1.4", name="spec.pdf"))
        recipe = make_recipe(make_item("Blend", code="BLEND"), [(self.assam, 1000)])
        from apps.inventory import services

        batch = services.make_blend(BlendBatch(recipe=recipe, quantity_made=100))
        order = PurchaseOrder.objects.create(supplier=self.supplier)
        PurchaseOrderLine.objects.create(order=order, item=self.assam, quantity=1000)
        receipt = Receipt.objects.create(supplier=self.supplier)
        pages = []
        for model in ["supplier", "item", "lot", "receipt", "purchaseorder", "stockadjustment", "stockmovement",
                      "recipe", "blendbatch", "allergen"]:
            pages += [reverse(f"admin:inventory_{model}_changelist"), reverse(f"admin:inventory_{model}_add")]
        pages = [p for p in pages if not p.endswith("stockmovement/add/")]
        pages += [
            reverse("admin:inventory_lot_change", args=[lot.pk]),
            reverse("admin:inventory_item_change", args=[self.assam.pk]),
            reverse("admin:inventory_blendbatch_change", args=[batch.pk]),
            reverse("admin:inventory_purchaseorder_change", args=[order.pk]),
            reverse("admin:inventory_receipt_change", args=[receipt.pk]),
            reverse("admin:inventory_recipe_change", args=[recipe.pk]),
            reverse("admin:inventory_item_changelist") + "?stock=low",
            reverse("admin:inventory_item_changelist") + "?stock=out",
            reverse("inventory:lot_trace", args=[lot.pk]),
        ]
        for page in pages:
            with self.subTest(page=page):
                self.assertEqual(self.client.get(page).status_code, 200)

    def test_item_list_shows_usable_stock_and_low_flag(self):
        make_lot(self.assam, 400)
        make_lot(self.assam, 900, status=Lot.Status.RECALLED)
        response = self.client.get(reverse("admin:inventory_item_changelist") + "?stock=low")
        self.assertContains(response, "400 g")
        self.assertNotContains(response, "Tin 100")

    def test_receive_delivery_with_two_lots(self):
        order = PurchaseOrder.objects.create(supplier=self.supplier, status=PurchaseOrder.Status.ORDERED)
        line = PurchaseOrderLine.objects.create(order=order, item=self.assam, quantity=5000)
        milk = Allergen.objects.get(code="milk")
        data = {
            "supplier": self.supplier.pk,
            "purchase_order": order.pk,
            "received_on": "2026-11-02",
            "notes": "",
            **inline_management("lots", total=2),
            "lots-0-item": self.assam.pk,
            "lots-0-purchase_order_line": line.pk,
            "lots-0-quantity_received": "3000",
            "lots-0-supplier_lot_code": "A-77",
            "lots-0-harvest_year": "2026",
            "lots-0-best_by": "2028-11-01",
            "lots-0-country_of_origin": "India",
            "lots-0-allergens": [milk.pk],
            "lots-0-landed_cost": "42.50",
            "lots-0-tariff_cost": "0",
            "lots-1-item": self.tin.pk,
            "lots-1-quantity_received": "200",
        }
        response = self.client.post(reverse("admin:inventory_receipt_add"), data)
        self.assertEqual(response.status_code, 302, response.context and response.context["adminform"].errors)
        receipt = Receipt.objects.get()
        tea_lot = receipt.lots.get(item=self.assam)
        self.assertEqual(tea_lot.code, "ASSAM-261102")
        self.assertEqual(tea_lot.quantity_on_hand, 3000)
        self.assertEqual(tea_lot.supplier, self.supplier)
        self.assertEqual(list(tea_lot.allergens.all()), [milk])
        self.assertEqual(receipt.lots.get(item=self.tin).quantity_on_hand, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, PurchaseOrder.Status.PARTIAL)

    def test_receive_bulk_lot_without_best_by_shows_error(self):
        data = {
            "supplier": self.supplier.pk,
            "received_on": "2026-11-02",
            **inline_management("lots", total=1),
            "lots-0-item": self.assam.pk,
            "lots-0-quantity_received": "3000",
        }
        response = self.client.post(reverse("admin:inventory_receipt_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bulk items need a best-by date")
        self.assertFalse(Lot.objects.exists())

    def test_stock_adjustment(self):
        lot = make_lot(self.assam, 1000)
        url = reverse("admin:inventory_stockadjustment_add")
        response = self.client.post(url, {"lot": lot.pk, "quantity": "-25", "reason": "sample", "note": "Fair"})
        self.assertEqual(response.status_code, 302)
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_on_hand, 975)
        movement = lot.movements.get(kind=StockMovement.Kind.ADJUSTMENT)
        self.assertEqual((movement.quantity, movement.reason, movement.note), (-25, "sample", "Fair"))

    def test_stock_adjustment_errors(self):
        lot = make_lot(self.assam, 10)
        url = reverse("admin:inventory_stockadjustment_add")
        response = self.client.post(url, {"lot": lot.pk, "quantity": "-25", "reason": "spoiled"})
        self.assertContains(response, "has only 10 g")
        response = self.client.post(url, {"lot": lot.pk, "quantity": "-5", "reason": ""})
        self.assertContains(response, "This field is required")
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_on_hand, 10)

    def test_make_blend_in_admin_with_auto_lots(self):
        blend = make_item("Blend", code="BLEND")
        recipe = make_recipe(blend, [(self.assam, 1000)])
        make_lot(self.assam, 1000)
        data = {
            "recipe": recipe.pk,
            "made_on": "2026-11-03",
            "quantity_made": "400",
            "best_by": "",
            "notes": "",
            **inline_management("inputs", total=4),
        }
        response = self.client.post(reverse("admin:inventory_blendbatch_add"), data)
        self.assertEqual(response.status_code, 302)
        batch = BlendBatch.objects.get()
        self.assertEqual(batch.output_lot.quantity_on_hand, 400)
        self.assertEqual(self.assam.on_hand(), 600)

    def test_make_blend_in_admin_shows_stock_problem(self):
        blend = make_item("Blend", code="BLEND")
        recipe = make_recipe(blend, [(self.assam, 1000)])
        lot = make_lot(self.assam, 100)
        data = {
            "recipe": recipe.pk,
            "made_on": "2026-11-03",
            "quantity_made": "400",
            **inline_management("inputs", total=1),
            "inputs-0-lot": lot.pk,
            "inputs-0-quantity": "400",
        }
        response = self.client.post(reverse("admin:inventory_blendbatch_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has only 100 g")
        self.assertFalse(BlendBatch.objects.exists())

    def test_recipe_components_must_total_1000(self):
        data = {
            "output_item": make_item("Blend", code="BLEND").pk,
            "name": "Blend recipe",
            "notes": "",
            "is_active": "on",
            **inline_management("components", total=1),
            "components-0-item": self.assam.pk,
            "components-0-grams_per_kg": "900",
        }
        response = self.client.post(reverse("admin:inventory_recipe_add"), data)
        self.assertContains(response, "add up to 900")

    def test_recall_action(self):
        lot = make_lot(self.assam, 1000)
        from apps.inventory import services

        services.post_movement(lot, -50, StockMovement.Kind.SALE, reference="A-1001")
        response = self.client.post(
            reverse("admin:inventory_lot_changelist"), {"action": "recall", "_selected_action": [lot.pk]}, follow=True
        )
        self.assertContains(response, "1 order(s) to contact: A-1001")
        lot.refresh_from_db()
        self.assertEqual(lot.status, Lot.Status.RECALLED)

    def test_document_download_owner_only(self):
        lot = make_lot(self.assam, 1000)
        document = LotDocument.objects.create(
            lot=lot, kind=LotDocument.Kind.SPEC_SHEET, file=ContentFile(b"%PDF-1.4 spec", name="spec.pdf")
        )
        url = document.file.url
        self.assertTrue(url.startswith("/owner/inventory/files/inventory/"), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("sandbox", response["Content-Security-Policy"])
        self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.4 spec")

        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_document_other_types_download(self):
        lot = make_lot(self.assam, 1000)
        document = LotDocument.objects.create(
            lot=lot, kind=LotDocument.Kind.OTHER, file=ContentFile(b"a,b", name="results.csv")
        )
        response = self.client.get(document.file.url)
        self.assertIn("attachment", response["Content-Disposition"])

    def test_document_path_traversal_and_missing(self):
        base = reverse("inventory:private_file", args=["x"])[:-1]
        self.assertEqual(self.client.get(base + "../../config/settings.py").status_code, 404)
        self.assertEqual(self.client.get(base + "nope.pdf").status_code, 404)

    def test_trace_page(self):
        lot = make_lot(self.assam, 1000, supplier=self.supplier, supplier_lot_code="SUP-9")
        response = self.client.get(reverse("inventory:lot_trace", args=[lot.pk]))
        self.assertContains(response, f"Trace for lot {lot.code}")
        self.assertContains(response, "supplier lot SUP-9")
        self.assertContains(response, "No orders have been packed from it.")

    def test_dashboard_shows_low_stock(self):
        response = self.client.get(reverse("core:owner_dashboard"))
        self.assertContains(response, "Low stock: 1 item")
        self.assertContains(response, "Assam (0 g)")


class LotDateTests(TestCase):
    def test_receipt_date_wins_for_lot(self):
        receipt = Receipt.objects.create(supplier=make_supplier(), received_on=date(2026, 5, 4))
        lot = make_lot(make_item("Assam"), 100, receipt=receipt)
        self.assertEqual(lot.received_on, date(2026, 5, 4))
