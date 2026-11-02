"""Operations events: deploys, rollbacks, backups and restore tests.

The deploy scripts and the backup timers record each run's result with
``manage.py record_ops_event`` (see deploy/record-ops-event.sh), so it
shows in the audit log and on the owner dashboard, not only in the
server's journal.  Each is an audit event whose action is
``ops.<kind>_<outcome>``, e.g. ``ops.backup_failed``.

Other apps add kinds of their own with register_kind() in their
AppConfig.ready() (the ops agent's health checks and upkeep, apps/ops), so
they show on the dashboard's Operations card and its attention list too.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from .context import Actor, acting_as
from .recording import record

SUCCEEDED = "succeeded"
FAILED = "failed"
OUTCOMES = (SUCCEEDED, FAILED)


@dataclass(frozen=True)
class OpsKind:
    name: str  # as given to record_ops_event
    title: str  # as the dashboard shows it
    actor_label: str  # the "who" of its audit events
    # A success older than this is overdue; None for things run by hand.
    expected_every: timedelta | None = None


KINDS = {
    kind.name: kind
    for kind in (
        OpsKind("deploy", "Deploy", "deploy script"),
        OpsKind("rollback", "Rollback", "rollback script"),
        # Daily timer; two days allows for one failed or late run.
        OpsKind("backup", "Off-site backup", "backup job", expected_every=timedelta(days=2)),
        # Monthly timer, on the 1st.
        OpsKind("restore_test", "Restore test", "restore test", expected_every=timedelta(days=33)),
    )
}


def register_kind(kind):
    """Add an OpsKind from another app (call in AppConfig.ready())."""
    KINDS[kind.name] = kind


def action_for(kind, outcome):
    return f"ops.{kind}_{outcome}"


def record_ops_event(kind, outcome, *, message="", commit="", details=None, actor=None):
    """Record one ops run's result as an audit event and return it: by the
    kind's system actor, or by `actor` (an AI agent recording its own run)."""
    if kind not in KINDS:
        raise ValueError(f"Unknown ops event kind {kind!r}; known: {', '.join(KINDS)}")
    if outcome not in OUTCOMES:
        raise ValueError(f"Unknown outcome {outcome!r}; use {' or '.join(OUTCOMES)}")
    info = KINDS[kind]
    changes = dict(details or {})
    if commit:
        changes["commit"] = commit
    message = message or f"{info.title} {outcome}"
    with acting_as(actor or Actor(type="system", label=info.actor_label)):
        return record(
            action_for(kind, outcome),
            message=message,
            changes=changes,
            object_type=f"ops.{kind}",
            object_id=commit,
        )


@dataclass(frozen=True)
class OpsStatus:
    kind: OpsKind
    last: object  # the latest AuditEvent of this kind, or None
    last_success: object  # the latest successful one, or None

    @property
    def failed(self):
        return self.last is not None and self.last.action == action_for(self.kind.name, FAILED)

    @property
    def overdue(self):
        """A scheduled job with no success recorded for longer than expected.
        False until the job has run at least once, so a new server or a
        development machine shows "never run", not an alarm."""
        if self.kind.expected_every is None or self.last is None:
            return False
        if self.last_success is None:
            return True
        return timezone.now() - self.last_success.timestamp > self.kind.expected_every

    @property
    def needs_attention(self):
        return self.failed or self.overdue


def ops_status():
    """The latest result of each kind of ops run, for the owner dashboard."""
    from .models import AuditEvent

    statuses = []
    for kind in KINDS.values():
        success_action = action_for(kind.name, SUCCEEDED)
        events = AuditEvent.objects.filter(action__in=[success_action, action_for(kind.name, FAILED)])
        last = events.first()
        if last is None or last.action == success_action:
            last_success = last
        else:
            last_success = events.filter(action=success_action).first()
        statuses.append(OpsStatus(kind, last, last_success))
    return statuses
