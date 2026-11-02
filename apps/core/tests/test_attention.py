from unittest import mock

from django.test import SimpleTestCase

from apps.core import attention
from apps.core.attention import Attention


class AttentionTests(SimpleTestCase):
    def test_urgent_first_and_failing_provider_logged(self):
        def ok():
            return [Attention("later"), Attention("now", level="urgent")]

        def broken():
            raise RuntimeError("boom")

        with mock.patch.object(attention, "_providers", []):
            attention.register(ok)
            attention.register(ok)  # registered once
            attention.register(broken)
            with self.assertLogs("apps.core.attention", level="ERROR") as logs:
                items = attention.collect()
        self.assertEqual([item.title for item in items], ["now", "later"])
        self.assertIn("boom", "\n".join(logs.output))

    def test_shortcut_groups_keep_order_add_queries_and_skip_bad_urls(self):
        with mock.patch.object(attention, "_shortcuts", []):
            attention.register_shortcut("Lots", "admin:inventory_lot_changelist", "Stock")
            attention.register_shortcut("Health", "ops:owner_home")
            attention.register_shortcut("Boxes", "admin:inventory_item_changelist", "Stock", query="kind__exact=box")
            attention.register_shortcut("Lots", "admin:inventory_lot_changelist", "Stock")  # registered once
            attention.register_shortcut("Gone", "no:such_url", "Stock")
            with self.assertLogs("apps.core.attention", level="ERROR"):
                groups = attention.shortcut_groups()
        self.assertEqual([group for group, _links in groups], ["", "Stock"])
        self.assertEqual([title for title, _url in groups[0][1]], ["Health"])
        stock = groups[1][1]
        self.assertEqual([title for title, _url in stock], ["Lots", "Boxes"])
        self.assertTrue(stock[1][1].endswith("/inventory/item/?kind__exact=box"))
