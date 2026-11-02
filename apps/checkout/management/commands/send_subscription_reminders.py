from django.core.management.base import BaseCommand

from apps.checkout import subscriptions


class Command(BaseCommand):
    help = ("Email renewal reminders for yearly subscriptions renewing in 15 to 30 days (NY GBL 527-a, "
            "California's automatic renewal law).  Run daily.")

    def handle(self, *args, **options):
        sent = subscriptions.send_reminders()
        self.stdout.write(f"Sent {sent} renewal reminder{'s' if sent != 1 else ''}.")
