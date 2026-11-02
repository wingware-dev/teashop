"""Fill a development database with the demo catalog and a sample
business around it (apps/storefront/demo_shop.py).  Refused unless DEBUG
is on, so it can never touch the live shop.  Safe to run more than once."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.storefront import demo_shop


class Command(BaseCommand):
    help = ("Load made-up teas, suppliers, lots, supplies, orders, a subscription, email subscribers, support "
            "and marketing content into a development database (DEBUG only; safe to run twice).")

    def handle(self, **options):
        if not settings.DEBUG or settings.PRODUCTION:
            raise CommandError("The sample shop data is invented; it is only loaded with DEBUG on, never on the "
                               "live shop.")
        demo_shop.load()
        self.stdout.write(self.style.SUCCESS(
            "Sample shop loaded.  Run the server, sign in with your createsuperuser account (two-factor login) and "
            "open the owner dashboard."))
