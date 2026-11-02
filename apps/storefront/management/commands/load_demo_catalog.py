"""Fill an empty development database with the demo catalog
(apps/storefront/demo.py) to try the shop with.  Refused in production."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.storefront import demo


class Command(BaseCommand):
    help = "Load a made-up demo catalog for trying the shop on a laptop (not in production)."

    def handle(self, **options):
        if settings.PRODUCTION:
            raise CommandError("The demo catalog is invented; it must never be loaded on the live shop.")
        demo.load()
        self.stdout.write(self.style.SUCCESS("Demo catalog loaded.  Run the server and open http://127.0.0.1:8000/"))
