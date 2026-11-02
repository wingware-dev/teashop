"""Record a development milestone: screenshots of every page in doc/shots/.

    python manage.py milestone_shots phase1-skeleton

runs the browser tests (tag "ui", see apps.core.uitesting) with their
screenshots going to doc/shots/<date>-<name>/ instead of var/shots/.  The
tests must pass; if any fail, nothing is left in the folder.  The shots
are then compressed losslessly with oxipng (requirements-ui.txt), since
they are kept in version control.
"""

import datetime
import os
import shutil

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.core.uitesting import MILESTONE_ENV, MILESTONE_NAME_RE, shots_dir

try:
    import oxipng
except ImportError:  # requirements-ui.txt not installed; handle() says so
    oxipng = None


def optimize_pngs(paths):
    """Recompress PNG files in place, losslessly (same pixels), and drop
    metadata that does not affect how they look.  Returns the bytes saved."""
    saved = 0
    for path in paths:
        before = path.stat().st_size
        oxipng.optimize(path, level=2, strip=oxipng.StripChunks.safe())
        saved += before - path.stat().st_size
    return saved


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
        if oxipng is None:
            raise CommandError("Needs oxipng to compress the shots: pip install -r requirements-ui.txt")
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
        saved = optimize_pngs(shots)
        size = sum(shot.stat().st_size for shot in shots)
        self.stdout.write(self.style.SUCCESS(
            f"{len(shots)} screenshots ({size / 1e6:.1f} MB, {saved / 1e6:.1f} MB saved by oxipng) "
            f"in {directory.relative_to(directory.parents[2])}"
        ))
