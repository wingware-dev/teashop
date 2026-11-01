"""Record a development milestone: screenshots of every page in doc/shots/.

    python manage.py milestone_shots phase1-skeleton

runs the browser tests (tag "ui", see apps.core.uitesting) with their
screenshots going to doc/shots/<date>-<name>/ instead of var/shots/.  The
tests must pass; if any fail, nothing is left in the folder.
"""

import datetime
import os
import shutil

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.core.uitesting import MILESTONE_ENV, MILESTONE_NAME_RE, shots_dir


class Command(BaseCommand):
    help = "Screenshot every page (phone/desktop, light/dark) into doc/shots/<date>-<name>/."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Milestone name, e.g. phase1-skeleton")
        parser.add_argument(
            "--date",
            default=datetime.date.today().isoformat(),
            help="Date for the folder name (default today, YYYY-MM-DD)",
        )
        parser.add_argument("labels", nargs="*", default=["apps"], help="Test labels to run (default: apps)")

    def handle(self, name, date, labels, **options):
        milestone = f"{date}-{name}"
        if not MILESTONE_NAME_RE.match(milestone):
            raise CommandError("Use lowercase letters, digits, '.', '_' and '-' in the name")
        old_env = os.environ.get(MILESTONE_ENV)
        os.environ[MILESTONE_ENV] = milestone
        try:
            directory = shots_dir()
            if directory.exists():
                # A re-run replaces the milestone's shots, so pages renamed
                # or removed since do not linger.
                shutil.rmtree(directory)
            try:
                call_command("test", *labels, tags=["ui"], interactive=False, verbosity=options["verbosity"])
            except SystemExit as exc:
                if exc.code:
                    shutil.rmtree(directory, ignore_errors=True)
                    raise CommandError("Browser tests failed; no milestone shots recorded") from exc
        finally:
            if old_env is None:
                os.environ.pop(MILESTONE_ENV, None)
            else:
                os.environ[MILESTONE_ENV] = old_env
        shots = sorted(directory.glob("*.png")) if directory.exists() else []
        if not shots:
            raise CommandError("The browser tests saved no screenshots (is Playwright installed?)")
        self.stdout.write(self.style.SUCCESS(f"{len(shots)} screenshots in {directory.relative_to(directory.parents[2])}"))
