"""The quarterly security review: a checklist the owner works through each
quarter (owner/ops/review/), with what the shop already knows filled in
beside each item.  docs/security/quarterly-review.md explains each item.

ITEMS: (key, title, what to do).  facts() gives the automatic facts:
{key: [(ok, text)]}, where ok is True (fine), False (look at it) or None
(for information).
"""

from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

ITEMS = [
    ("updates", "The server is up to date",
     "No security updates waiting, no restart pending, no failed services, and automatic updates ran this week "
     "(the server page shows each)."),
    ("backups", "Backups restore",
     "A restore test succeeded this quarter.  Once a year, restore a backup on a spare server yourself "
     "(docs/ops/backups.md)."),
    ("dependencies", "No known vulnerable packages",
     "GitHub: the latest CI run's \"Known vulnerabilities in dependencies\" step passed, and no Dependabot alerts "
     "or pull requests are waiting (repository > Security; Pull requests)."),
    ("code_review", "Changes had their security review",
     "GitHub Actions: read the \"Security review\" results of this quarter's changes; anything marked medium or "
     "high was fixed or explained."),
    ("outside_scan", "The outside scan is clean",
     "Run the \"Outside vulnerability scan\" workflow (GitHub > Actions) and read its report; check the site at "
     "ssllabs.com/ssltest (grade A) and securityheaders.com."),
    ("accounts", "Only the right people can sign in",
     "Every staff account below is someone who still needs it, and each has two-factor on.  Remove the rest "
     "in the admin (Users)."),
    ("ssh", "Only your keys open the server",
     "On the server: sudo cat /home/*/.ssh/authorized_keys.  You should recognise every key: yours, GitHub "
     "Actions' deploy key, the ops agent's.  Remove any other."),
    ("agents", "The AI agents did only what they should",
     "Skim owner/agents/: spending, and what the agents did.  Each agent that answers alone should still "
     "deserve to."),
    ("signins", "No sign-in attacks got through",
     "Failed sign-ins below; many from one place is an attack the lockout stopped.  A successful sign-in you "
     "don't recognise means: follow docs/security/breach-response.md."),
    ("secrets", "Secrets are where they belong",
     "/srv/teashop/.env is readable only by deploy (ls -l), your password manager has RESTIC_PASSWORD and the "
     "two-factor backup codes, and any key that may have leaked was replaced."),
    ("plan", "The breach plan still works",
     "Re-read docs/security/breach-response.md: the contacts and accounts in it are still right."),
    ("ubuntu", "Ubuntu is supported",
     "More than a year of security support left (below), or a move to a newer release planned."),
]
KEYS = [key for key, _, _ in ITEMS]


def quarter_of(day):
    return f"{day.year}-Q{(day.month - 1) // 3 + 1}"


def quarter_start(day):
    return date(day.year, 3 * ((day.month - 1) // 3) + 1, 1)


def _latest_health():
    from .models import ServerReport

    return ServerReport.objects.filter(kind=ServerReport.Kind.HEALTH, ok=True).first()


def facts(today=None):
    from apps.audit.models import AuditEvent
    from apps.audit.ops import ops_status

    from . import findings as rules

    today = today or timezone.localdate()
    found = {key: [] for key in KEYS}
    report = _latest_health()
    if report is None:
        found["updates"].append((None, "No server health reading yet (OPS_SERVER is off or the first check "
                                       "hasn't run)."))
        found["ubuntu"].append((None, "Not known until the first server health reading."))
    else:
        serious = [f for f in report.findings if f["level"] != "info" and not f["key"].startswith("os:")]
        found["updates"].append((not serious, f"Last reading {timezone.localtime(report.created_at):%b %-d, %-I:%M %p}"
                                 f": {report.summary}."))
        os_info = report.data.get("os") or {}
        ends = rules.SUPPORT_ENDS.get(os_info.get("version", ""))
        if ends:
            left = (ends - today).days
            found["ubuntu"].append((left > 365, f"{os_info.get('name')}: security support until {ends:%B %Y} "
                                                f"({left} days)."))
        else:
            found["ubuntu"].append((False, f"Unknown release {os_info.get('name', '')}".strip() + "."))

    statuses = {status.kind.name: status for status in ops_status()}
    restore = statuses.get("restore_test")
    start = quarter_start(today)
    if restore and restore.last_success and timezone.localdate(restore.last_success.timestamp) >= start:
        found["backups"].append((True, f"Restore test succeeded {restore.last_success.timestamp:%b %-d}."))
    elif restore and restore.last_success:
        found["backups"].append((False, f"Last restore test success {restore.last_success.timestamp:%b %-d, %Y}: "
                                        "not this quarter."))
    else:
        found["backups"].append((False, "No restore test has succeeded yet."))

    staff = get_user_model().objects.filter(is_active=True, is_staff=True).order_by("username")
    for user in staff:
        has_2fa = _has_two_factor(user)
        last = f"last signed in {user.last_login:%b %-d, %Y}" if user.last_login else "never signed in"
        found["accounts"].append((has_2fa, f"{user.get_username()}{' (superuser)' if user.is_superuser else ''}: "
                                           f"{'two-factor on' if has_2fa else 'NO two-factor'}, {last}."))
    if not staff:
        found["accounts"].append((None, "No staff accounts."))

    live = list(settings.AGENTS_LIVE)
    found["agents"].append((None, "Agents using the live AI: " + (", ".join(live) if live else "none (all on the free "
                                                                                                 "stand-in)") + "."))
    since = timezone.now() - timedelta(days=92)
    failed = AuditEvent.objects.filter(action="login_failed", timestamp__gte=since).count()
    found["signins"].append((None, f"{failed} failed sign-ins in the last 3 months."))
    return found


def _has_two_factor(user):
    from django_otp import devices_for_user

    return any(True for _ in devices_for_user(user, confirmed=True))


def current_review(today=None):
    from .models import QuarterlyReview

    return QuarterlyReview.objects.filter(quarter=quarter_of(today or timezone.localdate())).first()


def due(today=None):
    """The quarter's review is waiting: not done, and the quarter's first
    month (time to get to it) is over."""
    today = today or timezone.localdate()
    if current_review(today):
        return False
    return (today.month - 1) % 3 >= 1
