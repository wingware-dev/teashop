from django.core.management.base import BaseCommand

from apps.jobs import queue
from apps.jobs.worker import Worker


class Command(BaseCommand):
    help = ("Run background jobs (emails, daily jobs) until stopped: the worker service in compose.yaml.  "
            "See docs/jobs.md.")

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true",
                            help="Queue the schedules that are due, run every due job, then exit.")
        parser.add_argument("--schedules", action="store_true", help="List the periodic jobs and exit.")

    def handle(self, *args, once=False, schedules=False, **options):
        if schedules:
            from apps.jobs.models import Schedule

            rows = {row.name: row for row in Schedule.objects.all()}
            for entry in queue.schedules():
                row = rows.get(entry.name)
                when = f"next {row.next_run_at:%Y-%m-%d %H:%M %Z}" if row else "not seen by a worker yet"
                self.stdout.write(f"{entry.name}: {entry.spec} ({when})")
            return
        worker = Worker()
        if not once:
            worker.handle_signals()
        worker.run(once=once)
