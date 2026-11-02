from django.core.management.base import BaseCommand

from apps.checkout import subscriptions


class Command(BaseCommand):
    help = ("Queue renewal reminders for yearly subscriptions renewing in 15 to 30 days (NY GBL 527-a, "
            "California's automatic renewal law).  The job worker does this daily (apps/checkout/jobs.py); "
            "run it by hand to catch up.")

    def handle(self, *args, **options):
        queued = subscriptions.send_reminders()
        self.stdout.write(f"Queued {queued} renewal reminder{'s' if queued != 1 else ''}.")
