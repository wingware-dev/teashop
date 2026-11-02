"""The checkout rate limits live in the database cache, shared by all workers."""

from unittest import mock

from django.conf import settings
from django.core.cache.backends.db import DatabaseCache
from django.core.management import call_command
from django.db import connection
from django.test import RequestFactory, TestCase

from apps.checkout import protection

TABLE = settings.CACHES["default"]["LOCATION"]


def worker_cache():
    """A cache client of its own, as each gunicorn worker process has."""
    return DatabaseCache(TABLE, {})


class SharedRateLimitTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().post("/checkout/", REMOTE_ADDR="203.0.113.7")

    def over_limit_in(self, cache, limit):
        with mock.patch.object(protection, "cache", cache):
            return protection.over_limit(self.request, "shared-test", limit)

    def test_settings_use_the_database_cache(self):
        self.assertEqual(settings.CACHES["default"]["BACKEND"], "django.core.cache.backends.db.DatabaseCache")

    def test_two_workers_share_the_count(self):
        first, second = worker_cache(), worker_cache()
        self.assertIsNot(first, second)
        self.assertFalse(self.over_limit_in(first, limit=3))
        self.assertFalse(self.over_limit_in(second, limit=3))
        self.assertFalse(self.over_limit_in(first, limit=3))
        # The fourth submission is past the limit whichever worker gets it.
        self.assertTrue(self.over_limit_in(second, limit=3))
        self.assertEqual(first.get(f"checkout-limit:shared-test:{protection.client_ip(self.request)}"), 4)

    def test_migrate_creates_the_cache_table(self):
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE {connection.ops.quote_name(TABLE)}")
        self.assertNotIn(TABLE, connection.introspection.table_names())
        call_command("migrate", verbosity=0)
        self.assertIn(TABLE, connection.introspection.table_names())
