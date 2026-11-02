from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.fulfillment import summary


class Command(BaseCommand):
    help = ("Email the owner the day's new orders, orders near or past their promised ship date (FTC Mail Order "
            "Rule) and delay notices waiting for an answer.  Run daily at 6pm.")

    def handle(self, *args, **options):
        if not settings.OWNER_NOTIFY_EMAIL:
            self.stdout.write("OWNER_NOTIFY_EMAIL is not set: no summary sent.")
            return
        try:
            sent = summary.send()
        except summary.SummaryNotSent as exc:
            raise CommandError(str(exc)) from exc
        if sent is None:
            self.stdout.write("Nothing new: no summary sent.")
        else:
            self.stdout.write(f"Sent the summary: {len(sent.new_orders)} new order(s), {len(sent.to_pack)} to pack.")
