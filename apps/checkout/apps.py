from django.apps import AppConfig
from django.core.management import call_command
from django.db.models.signals import post_migrate


def create_cache_table(using, verbosity=1, **kwargs):
    """migrate also creates the database cache's table (settings.CACHES),
    which holds the rate limits in protection.py."""
    call_command("createcachetable", database=using, verbosity=verbosity)


class CheckoutConfig(AppConfig):
    name = "apps.checkout"
    label = "checkout"
    verbose_name = "Checkout and orders"

    def ready(self):
        from apps.core import attention

        from . import alerts, checks  # noqa: F401 (checks registers itself)

        attention.register(alerts.attention_items)
        attention.register_shortcut("Sales by state and sales tax", "checkout:sales_by_state")
        # Django sends post_migrate only to apps with models, as this one has.
        post_migrate.connect(create_cache_table, sender=self, dispatch_uid="checkout.create_cache_table")
