"""Record a deploy, rollback, backup or restore-test result in the audit log.

    python manage.py record_ops_event deploy succeeded --commit 0123abcd4567 \\
        --message "Deployed 0123abcd4567 (was 89abcdef0123)" --detail previous=89abcdef0123

Called by deploy/record-ops-event.sh from the deploy scripts and the backup
timers; see apps.audit.ops.
"""

from django.core.management.base import BaseCommand, CommandError

from apps.audit.ops import KINDS, OUTCOMES, record_ops_event

MAX_MESSAGE = 2000


def parse_detail(text):
    key, sep, value = text.partition("=")
    if not sep or not key:
        raise CommandError(f"--detail needs KEY=VALUE, not {text!r}")
    return key, value


class Command(BaseCommand):
    help = "Record a deploy, rollback, backup or restore-test result in the audit log."

    def add_arguments(self, parser):
        parser.add_argument("kind", choices=list(KINDS))
        parser.add_argument("outcome", choices=list(OUTCOMES))
        parser.add_argument("--message", default="", help="What happened, in a line")
        parser.add_argument("--commit", default="", help="The build's commit id, for deploys and rollbacks")
        parser.add_argument(
            "--detail", action="append", default=[], metavar="KEY=VALUE", help="Extra fact to store; repeatable"
        )

    def handle(self, kind, outcome, message, commit, detail, **options):
        details = dict(parse_detail(item) for item in detail)
        message = " ".join(message.split())[:MAX_MESSAGE]
        event = record_ops_event(kind, outcome, message=message, commit=commit.strip(), details=details)
        self.stdout.write(f"Recorded audit event {event.pk}: {event.action}")
