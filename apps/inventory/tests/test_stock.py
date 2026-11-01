from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.inventory import services, tracing
from apps.inventory.alerts import attention_items, low_stock_items, lots_near_best_by
from apps.inventory.models import (
    AppendOnlyError,
    BlendBatch,
    Item,
    Lot,
    PurchaseOrder,
    PurchaseOrderLine,
    Receipt,
    StockMovement,
)
from apps.inventory.testing import make_item, make_lot, make_recipe, make_supplier


class LotTests(TestCase):
    def setUp(self):
        self.assam = make_item("Assam")

    def test_new_lot_posts_receipt_movement(self):
        lot = make_lot(self.assam, 2500)
        self.assertEqual(lot.quantity_on_hand, 2500)
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_on_hand, 2500)
        movement = lot.movements.get()
        self.assertEqual((movement.kind, movement.quantity), (StockMovement.Kind.RECEIPT, 2500))

    def test_code_from_item_code_and_date_unique(self):
        first = make_lot(self.assam, received_on=date(2026, 11, 1))
        second = make_lot(self.assam, received_on=date(2026, 11, 1))
        self.assertEqual(first.code, "ASSAM-261101")
        self.assertEqual(second.code, "ASSAM-261101-2")

    def test_ingredients_default_from_item(self):
        self.assertEqual(make_lot(self.assam).ingredients, "black tea")

    def test_received_quantity_is_fixed(self):
        lot = make_lot(self.assam, 1000)
        lot.quantity_received = 900
        with self.assertRaises(ValidationError):
            lot.full_clean()
        with self.assertRaises(ValidationError):
            lot.save()

    def test_bulk_lot_needs_best_by_and_country(self):
        lot = Lot(item=self.assam, quantity_received=100)
        with self.assertRaises(ValidationError) as caught:
            lot.full_clean()
        self.assertIn("best_by", caught.exception.message_dict)
        self.assertIn("country_of_origin", caught.exception.message_dict)

    def test_unit_lot_needs_neither(self):
        tin = make_item("Tin 100", kind=Item.Kind.PACKAGING)
        Lot(item=tin, quantity_received=50).full_clean()

    def test_tariff_not_more_than_landed_cost(self):
        lot = Lot(item=self.assam, quantity_received=100, best_by=date(2028, 1, 1), country_of_origin="India",
                  landed_cost=Decimal("40"), tariff_cost=Decimal("50"))
        with self.assertRaises(ValidationError) as caught:
            lot.full_clean()
        self.assertIn("tariff_cost", caught.exception.message_dict)

    def test_lot_changes_are_audited(self):
        lot = make_lot(self.assam)
        self.assertTrue(AuditEvent.objects.filter(action="create", object_type="inventory.lot", object_id=str(lot.pk)).exists())
        self.assertTrue(AuditEvent.objects.filter(action="create", object_type="inventory.stockmovement").exists())


class MovementTests(TestCase):
    def setUp(self):
        self.assam = make_item("Assam")
        self.lot = make_lot(self.assam, 1000)

    def test_adjust_with_reason(self):
        services.adjust(self.lot, -30, StockMovement.Reason.SAMPLE, "Market samples")
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity_on_hand, 970)

    def test_adjust_needs_known_reason(self):
        with self.assertRaises(ValueError):
            services.adjust(self.lot, -1, "")
        with self.assertRaises(ValueError):
            services.adjust(self.lot, -1, "lost-in-space")

    def test_cannot_go_below_zero(self):
        with self.assertRaises(services.StockError):
            services.adjust(self.lot, -1001, StockMovement.Reason.UNKNOWN)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity_on_hand, 1000)

    def test_zero_quantity_refused(self):
        with self.assertRaises(ValueError):
            services.post_movement(self.lot, 0, StockMovement.Kind.SALE)

    def test_movements_are_append_only(self):
        movement = self.lot.movements.get()
        movement.note = "edited"
        with self.assertRaises(AppendOnlyError):
            movement.save()
        with self.assertRaises(AppendOnlyError):
            movement.delete()

    def test_held_lot_cannot_be_sold_but_can_be_written_off(self):
        self.lot.status = Lot.Status.ON_HOLD
        self.lot.save()
        with self.assertRaises(services.StockError):
            services.post_movement(self.lot, -10, StockMovement.Kind.SALE)
        services.adjust(self.lot, -1000, StockMovement.Reason.SPOILED)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity_on_hand, 0)


class ConsumeAndPickTests(TestCase):
    def setUp(self):
        self.tin = make_item("Tin 100", kind=Item.Kind.PACKAGING)
        self.assam = make_item("Assam")

    def test_consume_oldest_best_by_first_across_lots(self):
        later = make_lot(self.tin, 10, best_by=None)
        older = make_lot(self.assam, 0 + 5, best_by=date(2027, 1, 1))  # another item, ignored
        first = make_lot(self.tin, 3, received_on=date(2026, 1, 1))
        movements = services.consume(self.tin, 5, reference="ORDER-1")
        self.assertEqual([(m.lot_id, m.quantity) for m in movements], [(first.pk, -3), (later.pk, -2)])
        self.assertTrue(all(m.reference == "ORDER-1" for m in movements))
        older.refresh_from_db()
        self.assertEqual(older.quantity_on_hand, 5)

    def test_consume_short_takes_nothing(self):
        lot = make_lot(self.tin, 3)
        with self.assertRaises(services.StockError):
            services.consume(self.tin, 4)
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_on_hand, 3)

    def test_pick_lot_skips_remnant_and_held_lots(self):
        remnant = make_lot(self.assam, 20, best_by=date(2027, 1, 1))
        held = make_lot(self.assam, 500, best_by=date(2027, 2, 1), status=Lot.Status.ON_HOLD)
        good = make_lot(self.assam, 500, best_by=date(2027, 3, 1))
        self.assertEqual(services.pick_lot(self.assam, 50), good)
        self.assertEqual(services.pick_lot(self.assam, 20), remnant)
        self.assertNotEqual(services.pick_lot(self.assam, 50), held)

    def test_pick_lot_none_big_enough(self):
        make_lot(self.assam, 40)
        make_lot(self.assam, 40)
        with self.assertRaises(services.StockError):
            services.pick_lot(self.assam, 50)

    def test_on_hand_counts_usable_lots_only(self):
        make_lot(self.assam, 300)
        make_lot(self.assam, 200, status=Lot.Status.RECALLED)
        self.assertEqual(self.assam.on_hand(), 300)


class ReceivingTests(TestCase):
    def setUp(self):
        self.supplier = make_supplier()
        self.assam = make_item("Assam")
        self.tin = make_item("Tin 100", kind=Item.Kind.PACKAGING)
        self.order = PurchaseOrder.objects.create(supplier=self.supplier, status=PurchaseOrder.Status.ORDERED)
        self.tea_line = PurchaseOrderLine.objects.create(order=self.order, item=self.assam, quantity=5000)
        self.tin_line = PurchaseOrderLine.objects.create(order=self.order, item=self.tin, quantity=100)

    def receive(self, line, quantity, on=date(2026, 11, 1)):
        receipt = Receipt.objects.create(supplier=self.supplier, purchase_order=self.order, received_on=on)
        return make_lot(line.item, quantity, receipt=receipt, purchase_order_line=line)

    def test_partial_then_complete_delivery(self):
        lot = self.receive(self.tea_line, 3000)
        self.assertEqual(lot.supplier, self.supplier)
        self.assertEqual(lot.received_on, date(2026, 11, 1))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, PurchaseOrder.Status.PARTIAL)
        self.assertEqual(self.tea_line.quantity_outstanding(), 2000)

        self.receive(self.tea_line, 2000, on=date(2026, 11, 9))
        self.receive(self.tin_line, 100, on=date(2026, 11, 9))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, PurchaseOrder.Status.RECEIVED)
        self.assertEqual(self.assam.on_hand(), 5000)

    def test_lot_must_match_order_line_item(self):
        lot = Lot(item=self.tin, quantity_received=5, purchase_order_line=self.tea_line)
        with self.assertRaises(ValidationError) as caught:
            lot.full_clean()
        self.assertIn("purchase_order_line", caught.exception.message_dict)

    def test_receipt_order_must_be_same_supplier(self):
        other = make_supplier("Other")
        receipt = Receipt(supplier=other, purchase_order=self.order)
        with self.assertRaises(ValidationError):
            receipt.full_clean()

    def test_cancelled_order_stays_cancelled(self):
        self.order.status = PurchaseOrder.Status.CANCELLED
        self.order.save()
        self.receive(self.tea_line, 100)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, PurchaseOrder.Status.CANCELLED)


class BlendTests(TestCase):
    def setUp(self):
        self.assam = make_item("Assam")
        self.ceylon = make_item("Ceylon")
        self.vanilla = make_item("Vanilla flavour", code="VANILLA", kind=Item.Kind.INGREDIENT,
                                 ingredient_name="natural vanilla flavour")
        self.blend = make_item("Breakfast Vanilla", code="BRKV", ingredient_name="")
        self.recipe = make_recipe(self.blend, [(self.assam, 600), (self.ceylon, 380), (self.vanilla, 20)])
        self.assam_lot = make_lot(self.assam, 5000, best_by=date(2028, 3, 1), country="India",
                                  landed_cost=Decimal("40.00"), tariff_cost=Decimal("0"), organic=True)
        self.ceylon_lot = make_lot(self.ceylon, 5000, best_by=date(2027, 12, 1), country="Sri Lanka",
                                   landed_cost=Decimal("50.00"), tariff_cost=Decimal("0"), organic=True)
        self.vanilla_lot = make_lot(self.vanilla, 500, best_by=date(2027, 6, 1), landed_cost=Decimal("200.00"),
                                    tariff_cost=Decimal("10.00"), allergens=["milk"],
                                    allergen_statement="Contains milk derivatives")

    def batch(self, quantity=1000, **fields):
        return BlendBatch(recipe=self.recipe, quantity_made=quantity, made_on=date(2026, 11, 1), **fields)

    def test_make_blend_with_suggested_lots(self):
        batch = services.make_blend(self.batch(1000))
        lot = batch.output_lot
        self.assertEqual(lot.item, self.blend)
        self.assertEqual(lot.source, Lot.Source.BLENDED)
        self.assertEqual(lot.quantity_on_hand, 1000)
        self.assertEqual(lot.code, "BRKV-261101")
        self.assertEqual(lot.best_by, date(2027, 6, 1))
        self.assertEqual(lot.country_of_origin, "India, Sri Lanka")
        self.assertEqual(lot.ingredients, "black tea, natural vanilla flavour")
        self.assertFalse(lot.organic)
        self.assertEqual([a.code for a in lot.allergens.all()], ["milk"])
        self.assertIn("Contains milk derivatives", lot.allergen_statement)
        # 0.6 kg × 40 + 0.38 × 50 + 0.02 × 200 = 47.00 per kg
        self.assertEqual(lot.landed_cost, Decimal("47.00"))
        self.assertEqual(lot.tariff_cost, Decimal("0.20"))
        for source, used in [(self.assam_lot, 600), (self.ceylon_lot, 380), (self.vanilla_lot, 20)]:
            before = source.quantity_received
            source.refresh_from_db()
            self.assertEqual(source.quantity_on_hand, before - used)
        self.assertEqual(batch.movements.count(), 3)

    def test_blend_ingredient_names_differ_dedupes(self):
        self.ceylon.ingredient_name = "black tea"
        self.ceylon.save()
        lot = services.make_blend(self.batch()).output_lot
        self.assertEqual(lot.ingredients, "black tea, natural vanilla flavour")

    def test_explicit_inputs_and_weighing_loss(self):
        inputs = [(self.assam_lot, 610), (self.ceylon_lot, 385), (self.vanilla_lot, 21)]
        batch = services.make_blend(self.batch(1000), inputs)
        self.assertEqual([(i.lot_id, i.quantity) for i in batch.inputs.all()],
                         [(self.assam_lot.pk, 610), (self.ceylon_lot.pk, 385), (self.vanilla_lot.pk, 21)])

    def test_missing_component_refused(self):
        with self.assertRaises(ValidationError):
            services.make_blend(self.batch(), [(self.assam_lot, 600), (self.ceylon_lot, 400)])
        self.assertFalse(BlendBatch.objects.exists())

    def test_lot_not_in_recipe_refused(self):
        other = make_lot(make_item("Darjeeling"), 1000)
        with self.assertRaises(ValidationError):
            services.make_blend(self.batch(), [(self.assam_lot, 600), (self.ceylon_lot, 380),
                                               (self.vanilla_lot, 20), (other, 10)])

    def test_best_by_cannot_outlast_ingredients(self):
        with self.assertRaises(ValidationError):
            services.make_blend(self.batch(best_by=date(2028, 1, 1)))

    def test_recipe_must_total_1000(self):
        self.recipe.components.filter(item=self.vanilla).update(grams_per_kg=30)
        with self.assertRaises(ValidationError):
            services.make_blend(self.batch())

    def test_short_component_refused_and_nothing_taken(self):
        with self.assertRaises(services.StockError):
            services.make_blend(self.batch(30000))
        self.assam_lot.refresh_from_db()
        self.assertEqual(self.assam_lot.quantity_on_hand, 5000)

    def test_trace_forward_and_back_and_recall(self):
        blend_lot = services.make_blend(self.batch()).output_lot
        services.post_movement(blend_lot, -50, StockMovement.Kind.SALE, reference="1001")
        services.post_movement(self.assam_lot, -100, StockMovement.Kind.SALE, reference="1002")
        # A blend of the blend: traced through two levels.
        double = make_item("Double Blend", code="DBL")
        second_recipe = make_recipe(double, [(self.blend, 1000)])
        double_lot = services.make_blend(BlendBatch(recipe=second_recipe, quantity_made=200)).output_lot
        services.post_movement(double_lot, -25, StockMovement.Kind.SALE, reference="1003")

        trace = tracing.trace(self.assam_lot)
        self.assertEqual(trace.derived, [blend_lot, double_lot])
        self.assertEqual(trace.order_references(), ["1001", "1002", "1003"])
        self.assertEqual(set(tracing.source_lots(double_lot)),
                         {blend_lot, self.assam_lot, self.ceylon_lot, self.vanilla_lot})

        tracing.recall(self.assam_lot, "Supplier recall")
        for lot in (self.assam_lot, blend_lot, double_lot):
            lot.refresh_from_db()
            self.assertEqual(lot.status, Lot.Status.RECALLED)
        self.ceylon_lot.refresh_from_db()
        self.assertEqual(self.ceylon_lot.status, Lot.Status.ACTIVE)
        with self.assertRaises(services.StockError):
            services.pick_lot(self.blend, 10)


class AlertTests(TestCase):
    def test_low_stock(self):
        assam = make_item("Assam", reorder_level=1000)
        tin = make_item("Tin", kind=Item.Kind.PACKAGING, reorder_level=20)
        make_item("No alert", reorder_level=0)
        make_lot(assam, 900)
        make_lot(tin, 50)
        make_lot(tin, 50, status=Lot.Status.ON_HOLD)
        self.assertEqual([(i.name, n) for i, n in low_stock_items()], [("Assam", 900)])
        items = attention_items()
        self.assertEqual(items[0].title, "Low stock: 1 item")
        self.assertIn("Assam (900 g)", items[0].detail)
        self.assertEqual(items[0].level, "warning")

    def test_out_of_stock_is_urgent(self):
        make_item("Assam", reorder_level=1000)
        self.assertEqual(attention_items()[0].level, "urgent")

    def test_best_by_and_hold(self):
        assam = make_item("Assam")
        today = timezone.localdate()
        soon = make_lot(assam, 100, best_by=today + timedelta(days=10))
        make_lot(assam, 100, best_by=today + timedelta(days=200))
        past = make_lot(assam, 100, best_by=today - timedelta(days=1))
        make_lot(assam, 100, status=Lot.Status.ON_HOLD, status_note="Smells musty")
        self.assertEqual(list(lots_near_best_by()), [past, soon])
        titles = [(i.title, i.level) for i in attention_items()]
        self.assertIn((f"Lot {past.code} is past its best-by date ({past.best_by:%Y-%m-%d})", "urgent"), titles)
        self.assertTrue(any("is on hold" in title for title, _ in titles))
