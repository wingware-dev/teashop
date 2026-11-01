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
