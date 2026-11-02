from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.audit import acting_as_agent
from apps.core.testing import login_verified, make_owner
from apps.inventory import services as inventory
from apps.inventory.models import BlendBatch, Item, Lot, PurchaseOrder, PurchaseOrderLine, StockMovement
from apps.inventory.reorder import reorders
from apps.inventory.testing import make_item, make_lot, make_recipe, make_supplier
from apps.purchasing import reports, services
from apps.purchasing.alerts import attention_items
from apps.purchasing.models import StockCount

REORDER = dict(
    REORDER_USAGE_WINDOW_DAYS=90,
    REORDER_MIN_HISTORY_DAYS=14,
    REORDER_SAFETY_DAYS=10,
    REORDER_COVER_DAYS=60,
    REORDER_DEFAULT_LEAD_DAYS=20,
    BLEND_LEAD_DAYS=2,
)


def sell(lot, quantity, days_ago=0, reference="1001"):
    movement = inventory.post_movement(lot, -quantity, StockMovement.Kind.SALE, reference=reference)
    if days_ago:
        StockMovement.objects.filter(pk=movement.pk).update(created_at=timezone.now() - timedelta(days=days_ago))
    return movement


def reorder_for(item):
    return next(r for r in reorders() if r.item.pk == item.pk)


@override_settings(**REORDER)
class ReorderTests(TestCase):
    def setUp(self):
        self.supplier = make_supplier()
        self.supplier.lead_time_days = 30
        self.supplier.save()
        self.assam = make_item("Assam", default_supplier=self.supplier)
        self.lot = make_lot(self.assam, 20000, received_on=timezone.localdate() - timedelta(days=200))

    def test_daily_use_and_levels(self):
        sell(self.lot, 4500, days_ago=10)
        sell(self.lot, 4500, days_ago=80)
        sell(self.lot, 9000, days_ago=120)  # outside the 90-day window
        r = reorder_for(self.assam)
        self.assertEqual(r.daily_use, Decimal(100))  # 9000 g / 90 days
        self.assertEqual((r.lead_days, r.safety_days), (30, 10))
        self.assertEqual(r.level, 4000)  # 100 × (30 + 10)
        self.assertEqual(r.on_hand, 2000)
        self.assertTrue(r.needs_order)
        self.assertEqual(r.suggested, 100 * (30 + 10 + 60) - 2000)
        self.assertEqual(r.days_left, 20)
        self.assertTrue(self.assam.is_low())

    def test_losses_are_not_demand_but_samples_and_blends_are(self):
        inventory.adjust(self.lot, -9000, StockMovement.Reason.SPOILED)
        self.assertEqual(reorder_for(self.assam).daily_use, 0)
        inventory.adjust(self.lot, -900, StockMovement.Reason.SAMPLE)
        blend = make_item("Blend", code="BLEND")
        services_batch = BlendBatch(recipe=make_recipe(blend, [(self.assam, 1000)]), quantity_made=900)
        inventory.make_blend(services_batch)
        self.assertEqual(reorder_for(self.assam).daily_use, Decimal(20))  # 1800 g / 90 days

    def test_returned_stock_nets_out_of_use(self):
        sell(self.lot, 1800, days_ago=10, reference="1001")
        sell(self.lot, 900, days_ago=5, reference="1002")

        def give_back(quantity, reference):
            # As catalog.services.reverse_package records an unpacked order.
            return inventory.post_movement(
                self.lot, quantity, StockMovement.Kind.ADJUSTMENT,
                reason=StockMovement.Reason.RETURNED, reference=reference)

        give_back(900, "1002")
        self.assertEqual(reorder_for(self.assam).daily_use, Decimal(20))  # (2700 - 900) g / 90 days
        # Not reusable: returned, then written off as damaged, a loss and not demand.
        give_back(900, "1001")
        inventory.post_movement(self.lot, -900, StockMovement.Kind.ADJUSTMENT,
                                reason=StockMovement.Reason.DAMAGED, reference="1001")
        self.assertEqual(reorder_for(self.assam).daily_use, Decimal(10))  # 900 g / 90 days
        # A return for a sale before the window can't take use below nothing.
        give_back(5000, "0999")
        self.assertEqual(reorder_for(self.assam).daily_use, 0)

    def test_new_item_measured_since_first_delivery(self):
        tin = make_item("Tin", kind=Item.Kind.PACKAGING)
        lot = make_lot(tin, 100, received_on=timezone.localdate() - timedelta(days=5))
        sell(lot, 28)
        # 5 days of history counts as the 14-day minimum: 2 a day.
        self.assertEqual(reorder_for(tin).daily_use, Decimal(2))

    def test_fixed_level_is_floor_and_on_order_counts(self):
        self.assam.reorder_level = 25000
        self.assam.save()
        r = reorder_for(self.assam)
        self.assertEqual(r.level, 25000)
        self.assertEqual(r.suggested, 50000 - 20000)  # no use yet: back up to twice the level
        order = PurchaseOrder.objects.create(supplier=self.supplier, status=PurchaseOrder.Status.ORDERED)
        PurchaseOrderLine.objects.create(order=order, item=self.assam, quantity=10000)
        draft = PurchaseOrder.objects.create(supplier=self.supplier)
        PurchaseOrderLine.objects.create(order=draft, item=self.assam, quantity=99999)  # drafts don't count
        r = reorder_for(self.assam)
        self.assertEqual(r.on_order, 10000)
        self.assertEqual(r.suggested, 20000)

    def test_minimum_order_rounds_up(self):
        sell(self.lot, 18000, days_ago=1)
        self.assam.minimum_order = 5000
        self.assam.save()
        r = reorder_for(self.assam)
        self.assertEqual(r.suggested % 5000, 0)
        self.assertGreaterEqual(r.suggested, 5000)

    def test_auto_off_uses_fixed_level_only(self):
        sell(self.lot, 18000, days_ago=1)
        self.assam.auto_reorder = False
        self.assam.save()
        r = reorder_for(self.assam)
        self.assertEqual((r.daily_use, r.level, r.is_low), (0, 0, False))

    def test_default_lead_time_and_blends(self):
        self.supplier.lead_time_days = None
        self.supplier.save()
        self.assertEqual(reorder_for(self.assam).lead_days, 20)
        blend = make_item("Blend", code="BLEND")
        make_recipe(blend, [(self.assam, 1000)])
        r = reorder_for(blend)
        self.assertEqual((r.made_here, r.lead_days), (True, 2))


@override_settings(**REORDER)
class DraftAndApproveTests(TestCase):
    def setUp(self):
        self.owner, _ = make_owner()
        self.leaf = make_supplier("Leaf Importers")
        self.tins = make_supplier("Tin Works")
        self.assam = make_item("Assam", default_supplier=self.leaf, reorder_level=1000)
        self.ceylon = make_item("Ceylon", default_supplier=self.leaf, reorder_level=1000)
        self.tin = make_item("Tin", kind=Item.Kind.PACKAGING, default_supplier=self.tins, reorder_level=10)
        self.orphan = make_item("Orphan", reorder_level=10)
        blend = make_item("Blend", code="BLEND", reorder_level=100)
        make_recipe(blend, [(self.assam, 1000)])
        old = PurchaseOrder.objects.create(supplier=self.leaf, status=PurchaseOrder.Status.RECEIVED)
        PurchaseOrderLine.objects.create(order=old, item=self.assam, quantity=1, unit_cost=Decimal("38.50"))

    def test_draft_one_order_per_supplier(self):
        result = services.draft_purchase_orders()
        self.assertEqual(len(result.orders), 2)
        leaf = PurchaseOrder.objects.get(supplier=self.leaf, status=PurchaseOrder.Status.DRAFT)
        self.assertEqual(leaf.source, PurchaseOrder.Source.SUGGESTED)
        lines = {line.item.name: line for line in leaf.lines.all()}
        self.assertEqual(sorted(lines), ["Assam", "Ceylon"])
        self.assertEqual(lines["Assam"].quantity, 2000)
        self.assertEqual(lines["Assam"].unit_cost, Decimal("38.50"))
        self.assertIsNone(lines["Ceylon"].unit_cost)
        self.assertEqual([r.item.name for r in result.no_supplier], ["Orphan"])
        self.assertEqual([r.item.name for r in result.blends], ["Blend"])

        again = services.draft_purchase_orders()
        self.assertEqual(again.lines, [])
        self.assertEqual(len(again.already_drafted), 3)
        self.assertEqual(PurchaseOrder.objects.filter(status=PurchaseOrder.Status.DRAFT).count(), 2)

    def test_approve(self):
        self.leaf.lead_time_days = 14
        self.leaf.save()
        services.draft_purchase_orders()
        order = PurchaseOrder.objects.get(supplier=self.leaf, status=PurchaseOrder.Status.DRAFT)
        inventory.approve_purchase_order(order, self.owner)
        order.refresh_from_db()
        self.assertEqual(order.status, PurchaseOrder.Status.ORDERED)
        self.assertEqual(order.approved_by, self.owner)
        self.assertEqual(order.ordered_on, timezone.localdate())
        self.assertEqual(order.expected_on, timezone.localdate() + timedelta(days=14))
        self.assertEqual(reorder_for(self.assam).on_order, 2000)
        with self.assertRaises(ValidationError):
            inventory.approve_purchase_order(order, self.owner)

    def test_only_owner_approves(self):
        order = PurchaseOrder.objects.create(supplier=self.leaf)
        PurchaseOrderLine.objects.create(order=order, item=self.assam, quantity=5)
        with acting_as_agent("purchasing-agent"):
            services.draft_purchase_orders()  # agents may draft
            with self.assertRaises(PermissionDenied):
                inventory.approve_purchase_order(order, self.owner)
        customer, _ = make_owner("customer", staff=False, superuser=False)
        with self.assertRaises(PermissionDenied):
            inventory.approve_purchase_order(order, customer)
        empty = PurchaseOrder.objects.create(supplier=self.leaf)
        with self.assertRaises(ValidationError):
            inventory.approve_purchase_order(empty, self.owner)

    def test_cannot_receive_against_draft(self):
        order = PurchaseOrder.objects.create(supplier=self.leaf)
        line = PurchaseOrderLine.objects.create(order=order, item=self.assam, quantity=5)
        lot = Lot(item=self.assam, quantity_received=5, best_by=date(2028, 1, 1), country_of_origin="India",
                  purchase_order_line=line)
        with self.assertRaises(ValidationError) as caught:
            lot.full_clean()
        self.assertIn("approve it before receiving", str(caught.exception))

    def test_alerts(self):
        titles = [item.title for item in attention_items()]
        self.assertIn("Reorder: 4 items with no purchase order yet", titles)
        self.assertTrue(any(t.startswith("Make a blend batch: Blend") for t in titles))
        services.draft_purchase_orders()
        titles = [item.title for item in attention_items()]
        self.assertIn("Reorder: 1 item with no purchase order yet", titles)  # the orphan
        self.assertIn("Purchase order for Leaf Importers waits for your approval", titles)

        order = PurchaseOrder.objects.get(supplier=self.tins)
        inventory.approve_purchase_order(order, self.owner)
        PurchaseOrder.objects.filter(pk=order.pk).update(expected_on=timezone.localdate() - timedelta(days=1))
        late = [item for item in attention_items() if item.title.startswith("Delivery late")]
        self.assertEqual(late[0].level, "urgent")


class StockCountTests(TestCase):
    def setUp(self):
        self.owner, _ = make_owner()
        self.assam = make_item("Assam")
        self.tin = make_item("Tin", kind=Item.Kind.PACKAGING)
        self.lot = make_lot(self.assam, 1000)
        self.tin_lot = make_lot(self.tin, 50)
        make_lot(self.assam, 100, status=Lot.Status.RECALLED)
        empty = make_lot(self.assam, 10)
        inventory.adjust(empty, -10, StockMovement.Reason.COUNT)

    def lines(self, count):
        return {line.lot_id: line for line in count.lines.all()}

    def test_start_snapshots_lots_with_stock(self):
        count = services.start_count()
        self.assertEqual({lot_id: line.expected for lot_id, line in self.lines(count).items()},
                         {self.lot.pk: 1000, self.tin_lot.pk: 50})
        teas = services.start_count([Item.Kind.TEA])
        self.assertEqual(list(self.lines(teas)), [self.lot.pk])
        self.assertEqual(teas.kind_labels(), "Tea (bulk, by weight)")

    def test_apply_differences_with_reasons(self):
        count = services.start_count()
        sell(self.lot, 100)  # packed while counting: not a difference
        lines = self.lines(count)
        lines[self.lot.pk].counted = 960
        lines[self.lot.pk].reason = StockMovement.Reason.SPOILED
        lines[self.lot.pk].note = "Damp corner"
        lines[self.lot.pk].save()
        lines[self.tin_lot.pk].counted = 52
        lines[self.tin_lot.pk].save()
        movements = services.apply_count(count, self.owner)
        self.assertEqual(sorted((m.quantity, m.reason) for m in movements), [(-40, "spoiled"), (2, "count")])
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity_on_hand, 860)
        self.assertIn("Damp corner", self.lines(count)[self.lot.pk].movement.note)
        count.refresh_from_db()
        self.assertEqual((count.status, count.applied_by), (StockCount.Status.APPLIED, self.owner))
        with self.assertRaises(ValidationError):
            services.apply_count(count, self.owner)

    def test_shortage_needs_reason_and_nothing_applied(self):
        count = services.start_count()
        lines = self.lines(count)
        lines[self.tin_lot.pk].counted = 60
        lines[self.tin_lot.pk].save()
        lines[self.lot.pk].counted = 900
        lines[self.lot.pk].save()
        with self.assertRaises(ValidationError) as caught:
            services.apply_count(count, self.owner)
        self.assertIn("Say why it is short", str(caught.exception))
        self.tin_lot.refresh_from_db()
        self.assertEqual(self.tin_lot.quantity_on_hand, 50)

    def test_surplus_cannot_be_spoilage(self):
        count = services.start_count()
        line = self.lines(count)[self.tin_lot.pk]
        line.counted, line.reason = 60, StockMovement.Reason.SPOILED
        with self.assertRaises(ValidationError):
            line.full_clean()

    def test_stock_used_since_start_cannot_go_negative(self):
        count = services.start_count()
        sell(self.tin_lot, 50)
        line = self.lines(count)[self.tin_lot.pk]
        line.counted, line.reason = 10, StockMovement.Reason.UNKNOWN
        line.save()
        with self.assertRaises(ValidationError) as caught:
            services.apply_count(count, self.owner)
        self.assertIn("recount", str(caught.exception))
        count.refresh_from_db()
        self.assertEqual(count.status, StockCount.Status.OPEN)

    def test_agent_cannot_apply(self):
        count = services.start_count()
        with acting_as_agent("ops-agent"), self.assertRaises(PermissionDenied):
            services.apply_count(count, self.owner)


class ReportTests(TestCase):
    def setUp(self):
        self.assam = make_item("Assam")
        self.lot = make_lot(self.assam, 5000, landed_cost=Decimal("40.00"), tariff_cost=Decimal("4.00"))
        self.free = make_lot(make_item("Gift tea", code="GIFT"), 500)  # no landed cost

    def adjust(self, lot, quantity, reason, months_ago=0):
        movement = inventory.adjust(lot, quantity, reason)
        if months_ago:
            day = reports.add_months(timezone.localdate().replace(day=15), -months_ago)
            moved = timezone.make_aware(timezone.datetime(day.year, day.month, day.day, 12))
            StockMovement.objects.filter(pk=movement.pk).update(created_at=moved)

    def test_loss_trend(self):
        self.adjust(self.lot, -100, StockMovement.Reason.SPOILED)  # $4.00
        self.adjust(self.lot, -50, StockMovement.Reason.UNKNOWN)  # $2.00
        self.adjust(self.lot, 25, StockMovement.Reason.COUNT)  # -$1.00
        self.adjust(self.lot, -25, StockMovement.Reason.SAMPLE)  # $1.00 marketing
        self.adjust(self.lot, -10, StockMovement.Reason.PERSONAL)  # $0.40
        self.adjust(self.lot, -200, StockMovement.Reason.DAMAGED, months_ago=2)  # $8.00
        self.adjust(self.free, -5, StockMovement.Reason.SPOILED)
        self.adjust(self.lot, -1, StockMovement.Reason.SPOILED, months_ago=13)  # outside
        rows, worst = reports.loss_trend(12)
        self.assertEqual(len(rows), 12)
        this, two_ago = rows[-1], rows[-3]
        self.assertEqual(this.loss, Decimal("5.00"))
        self.assertEqual(this.by_reason["spoiled"], Decimal("4.00"))
        self.assertEqual(this.by_reason["count"], Decimal("-1.00"))
        self.assertEqual(this.marketing, Decimal("1.00"))
        self.assertEqual(this.personal, Decimal("0.40"))
        self.assertEqual(this.uncosted, 1)
        self.assertEqual(two_ago.loss, Decimal("8.00"))
        self.assertEqual([(w.item.name, w.quantity, w.cost) for w in worst],
                         [("Assam", 325, Decimal("13.00")), ("Gift tea", 5, Decimal("0.00"))])
        today = timezone.localdate()
        self.assertEqual(reports.marketing_cost(today.replace(day=1), today + timedelta(days=1)), Decimal("1.00"))

    def test_profitability(self):
        from apps.catalog import services as catalog
        from apps.catalog.models import BomLine, Product, SizeOption

        tin = make_item("Tin", kind=Item.Kind.PACKAGING)
        make_lot(tin, 10, landed_cost=Decimal("1.00"))
        make_lot(tin, 30, landed_cost=Decimal("2.00"))  # average 1.75
        product = Product.objects.create(name="Assam", slug="assam", tea=self.assam)
        small = SizeOption.objects.create(product=product, name="50 g tin", sku="A50", net_grams=50, price=Decimal("12"))
        large = SizeOption.objects.create(product=product, name="100 g tin", sku="A100", net_grams=100, price=Decimal("20"))
        for size in (small, large):
            BomLine.objects.create(size_option=size, item=tin)
        catalog.pack(small, "1001", tea_grams=52)
        catalog.pack(small, "1002")
        catalog.pack(large, "1002", amount="18.00")
        today = timezone.localdate()
        by_tea, by_size, total = reports.profitability(today, today + timedelta(days=1))
        self.assertEqual(len(by_tea), 1)
        tea = by_tea[0]
        self.assertEqual((tea.label, tea.packages, tea.grams), ("Assam", 3, 202))
        self.assertEqual(tea.revenue, Decimal("42.00"))
        self.assertEqual(tea.tea_cost, Decimal("8.08"))  # 202 g × $0.04
        self.assertEqual(tea.tariffs, Decimal("0.81"))
        self.assertEqual(tea.packaging_cost, Decimal("5.25"))
        self.assertEqual(tea.margin, Decimal("28.67"))
        self.assertEqual(tea.margin_percent, Decimal("68.3"))
        self.assertEqual([row.label for row in by_size], ["Assam 50 g tin (A50)", "Assam 100 g tin (A100)"])
        self.assertEqual(total.revenue, Decimal("42.00"))
        self.assertEqual(total.uncosted, 0)
        self.assertEqual(reports.profitability(today - timedelta(days=9), today)[2].packages, 0)

    def test_stock_value(self):
        self.assertEqual(reports.stock_value(), (Decimal("200.00"), 1))


class PageTests(TestCase):
    def setUp(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        self.supplier = make_supplier()
        self.assam = make_item("Assam", default_supplier=self.supplier, reorder_level=1000)
        self.lot = make_lot(self.assam, 500, landed_cost=Decimal("40"))

    def test_pages_need_owner(self):
        self.client.logout()
        for name in ("reorder", "losses", "profit"):
            self.assertEqual(self.client.get(reverse(f"purchasing:{name}")).status_code, 302)

    def test_reorder_page_and_draft(self):
        response = self.client.get(reverse("purchasing:reorder"))
        self.assertContains(response, "1 item is at or below the reorder level")
        self.assertContains(response, "500 g (low)")
        response = self.client.post(reverse("purchasing:reorder"), follow=True)
        self.assertContains(response, "Drafted 1 line(s) on 1 purchase order(s)")
        self.assertEqual(PurchaseOrderLine.objects.get().quantity, 1500)

    def test_losses_and_profit_pages(self):
        inventory.adjust(self.lot, -20, StockMovement.Reason.DAMAGED)
        self.assertContains(self.client.get(reverse("purchasing:losses")), "Loss $0.80")
        response = self.client.get(reverse("purchasing:profit") + "?start=2026-01-01&end=bad")
        self.assertContains(response, "Nothing packed in this period.")
        self.assertContains(response, "Stock on hand is worth $19.20")

    def test_po_approve_button(self):
        order = PurchaseOrder.objects.create(supplier=self.supplier)
        line = PurchaseOrderLine.objects.create(order=order, item=self.assam, quantity=1000)
        url = reverse("admin:inventory_purchaseorder_change", args=[order.pk])
        page = self.client.get(url)
        self.assertContains(page, "Save, approve and mark ordered")
        self.assertContains(page, "nothing is ordered until you approve it")
        data = {
            "supplier": self.supplier.pk, "reference": "PO-7", "ordered_on": "", "expected_on": "", "notes": "",
            "lines-TOTAL_FORMS": "1", "lines-INITIAL_FORMS": "1", "lines-MIN_NUM_FORMS": "0", "lines-MAX_NUM_FORMS": "1000",
            "lines-0-id": line.pk, "lines-0-order": order.pk, "lines-0-item": self.assam.pk,
            "lines-0-quantity": "1200", "lines-0-unit_cost": "41.00",
            "_approve": "Save, approve and mark ordered",
        }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "approved.  Send it to the supplier.")
        order.refresh_from_db()
        self.assertEqual((order.status, order.reference), (PurchaseOrder.Status.ORDERED, "PO-7"))
        self.assertEqual(order.lines.get().quantity, 1200)
        self.assertContains(self.client.get(url), "Record a delivery for this order")

    def test_stock_count_admin_flow(self):
        response = self.client.post(reverse("admin:purchasing_stockcount_add"), {"kinds": ["tea"], "notes": "Monthly"})
        self.assertEqual(response.status_code, 302)
        count = StockCount.objects.get()
        line = count.lines.get()
        url = reverse("admin:purchasing_stockcount_change", args=[count.pk])
        self.assertContains(self.client.get(url), "Save and apply count")
        data = {
            "notes": "Monthly",
            "lines-TOTAL_FORMS": "1", "lines-INITIAL_FORMS": "1", "lines-MIN_NUM_FORMS": "0", "lines-MAX_NUM_FORMS": "1000",
            "lines-0-id": line.pk, "lines-0-count": count.pk,
            "lines-0-counted": "480", "lines-0-reason": "", "lines-0-note": "",
            "_apply": "Save and apply count",
        }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "Say why it is short")
        data["lines-0-reason"] = "personal"
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "Count applied: 1 adjustment(s) recorded.")
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity_on_hand, 480)
        self.assertNotContains(self.client.get(url), "Save and apply count")

    def test_dashboard_shortcuts_and_alerts(self):
        response = self.client.get(reverse("core:owner_dashboard"))
        self.assertContains(response, reverse("purchasing:reorder"))
        self.assertContains(response, "Profit per tea and per size")
        self.assertContains(response, "Reorder: 1 item with no purchase order yet")

    def test_item_admin_shows_auto_level(self):
        sell(self.lot, 450, days_ago=1)
        response = self.client.get(reverse("admin:inventory_item_changelist") + "?stock=low")
        self.assertContains(response, "Assam")
        self.assertContains(response, "(auto)")
