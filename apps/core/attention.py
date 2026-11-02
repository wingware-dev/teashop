"""The owner dashboard's "Needs your attention" queue.

core depends on no feature app, so feature apps register a provider in
their AppConfig.ready()::

    from apps.core import attention
    attention.register(my_provider)

A provider takes no arguments and returns a list of Attention items.  A
provider that fails is logged and skipped, so one broken app cannot take
the dashboard down.

Each item has a kind (KINDS: support, refunds, posts, orders, ...), and each kind
a deadline: how long an item may wait before the owner is reminded by
email (settings.ATTENTION_DEADLINES can change them).  An item is waiting
since its ``since`` (when the provider knows, e.g. when a purchase order
was drafted), else since the queue first saw it; queue() keeps that in
AttentionRecord, keyed by the item's ``key``.  Give a key that stays the
same while the item stays the same thing ("purchasing:po:12"), not one
that holds a count, or the clock restarts whenever the count changes.

The reminder emails themselves are sent by the reports app's jobs
(apps/reports/reminders.py), since core can't send email.

Apps add links to the dashboard's Shortcuts card the same way, with
register_shortcut(title, url_name).
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

log = logging.getLogger(__name__)

_providers = []


@dataclass(frozen=True)
class Attention:
    title: str
    detail: str = ""
    url: str = ""
    # "warning" for things to act on soon, "urgent" for things to act on now.
    level: str = "warning"
    # One of KINDS: decides the deadline before a reminder.
    kind: str = "other"
    # Stays the same while the item is the same thing; default kind:title.
    key: str = ""
    # When it began waiting, if the provider knows (an aware datetime).
    since: datetime | None = None

    @property
    def identity(self):
        return (self.key or f"{self.kind}:{self.title}")[:200]


@dataclass(frozen=True)
class Kind:
    name: str
    title: str
    # The default deadline: "0" (remind at once), "30m", "4h", "3d", "daily"
    # (in the daily reminder) or "HH:MM" (each day at that time).
    deadline: str
    # Set when another email than the reminders covers the kind.
    reminded_by: str = ""


KINDS = {
    kind.name: kind
    for kind in (
        Kind("support", "Support escalations", "0"),
        Kind("refunds", "Refunds and cancellations", "4h"),
        Kind("problems", "Things that are broken", "1h"),
        Kind("jobs", "Failed jobs and backups", "1h"),
        # Fulfillment's 6pm order summary is the orders' reminder.
        Kind("orders", "Orders", "18:00", reminded_by="the 6pm order summary"),
        Kind("posts", "Posts to put up by hand", "1h"),
        Kind("approvals", "Posts and designs to approve", "3d"),
        Kind("purchase_orders", "Purchase orders", "daily"),
        Kind("stock", "Stock", "daily"),
        Kind("other", "Other", "daily"),
    )
}


def kind_of(item):
    return KINDS.get(item.kind) or KINDS["other"]


_DURATION = re.compile(r"^(\d+)\s*([mhd]?)$")
_UNITS = {"": "minutes", "m": "minutes", "h": "hours", "d": "days"}


@dataclass(frozen=True)
class Deadline:
    after: timedelta | None = None  # remind once the item has waited this long
    at: time | None = None  # or: remind each day at this time

    @classmethod
    def parse(cls, spec):
        spec = str(spec).strip().lower()
        if spec == "daily":
            spec = settings.ATTENTION_DAILY_AT
        if ":" in spec:
            hour, minute = spec.split(":")
            return cls(at=time(int(hour), int(minute)))
        match = _DURATION.match(spec)
        if not match:
            raise ValueError(f"Not a deadline: {spec!r} (use 0, 30m, 4h, 3d, daily or HH:MM)")
        return cls(after=timedelta(**{_UNITS[match[2]]: int(match[1])}))

    def due(self, since):
        """When an item waiting since `since` should be reminded of."""
        if self.after is not None:
            return since + self.after
        local = timezone.localtime(since)
        due = timezone.make_aware(datetime.combine(local.date(), self.at))
        return due if due > since else timezone.make_aware(datetime.combine(local.date() + timedelta(days=1), self.at))

    def describe(self):
        if self.after is not None:
            if not self.after:
                return "Reminder at once"
            hours = self.after.total_seconds() / 3600
            if hours < 1:
                return f"Reminder after {int(self.after.total_seconds() // 60)} minutes"
            if hours < 48 or hours % 24:
                return f"Reminder after {hours:g} hour{'s' if hours != 1 else ''}"
            return f"Reminder after {int(hours // 24)} days"
        return f"Reminder each day at {self.at.strftime('%-I:%M %p').lower().replace(':00', '')}"


def deadline_for(kind_name):
    kind = KINDS.get(kind_name) or KINDS["other"]
    return Deadline.parse(settings.ATTENTION_DEADLINES.get(kind.name, kind.deadline))


def register(provider):
    if provider not in _providers:
        _providers.append(provider)


def collect():
    items = []
    for provider in _providers:
        try:
            items.extend(provider())
        except Exception:
            log.exception("Attention provider %r failed", provider)
    items.sort(key=lambda item: item.level != "urgent")
    return items


@dataclass
class Entry:
    """An item in the queue with its clock: waiting since, due (the
    reminder's time) and whether it is overdue."""

    item: Attention
    kind: Kind
    deadline: Deadline
    since: datetime
    due: datetime
    overdue: bool
    record: object  # its AttentionRecord

    @property
    def reminded_at(self):
        return self.record.reminded_at


def queue(now=None):
    """Every item now waiting, as Entry, overdue first, then urgent, then by
    due time.  Keeps AttentionRecord in step: new items get one, gone ones
    lose theirs (so if one comes back, its clock starts again)."""
    from .models import AttentionRecord

    now = now or timezone.now()
    items = {}
    for item in collect():
        items.setdefault(item.identity, item)  # the same key twice: the first (urgent) wins
    records = {record.key: record for record in AttentionRecord.objects.all()}
    gone = [key for key in records if key not in items]
    if gone:
        AttentionRecord.objects.filter(key__in=gone).delete()
    entries = []
    for key, item in items.items():
        record = records.get(key)
        if record is None:
            record, _ = AttentionRecord.objects.get_or_create(
                key=key, defaults={"kind": item.kind, "title": item.title[:300], "first_seen": now})
        elif record.title != item.title[:300] or record.kind != item.kind:
            record.title, record.kind = item.title[:300], item.kind
            record.save(update_fields=["title", "kind"])
        since = min(item.since, record.first_seen) if item.since else record.first_seen
        deadline = deadline_for(item.kind)
        due = deadline.due(since)
        entries.append(Entry(item, kind_of(item), deadline, since, due, due <= now, record))
    entries.sort(key=lambda e: (not e.overdue, e.item.level != "urgent", e.due))
    return entries


def grouped(entries):
    """[(Kind, Deadline, [Entry])] in KINDS order, for the kinds with items."""
    by_kind = {}
    for entry in entries:
        by_kind.setdefault(entry.kind.name, []).append(entry)
    return [(kind, deadline_for(kind.name), by_kind[kind.name]) for kind in KINDS.values() if kind.name in by_kind]


# Links for the dashboard's Shortcuts card, as (title, URL name), so feature
# apps can add their back-office pages without core naming them.
_shortcuts = []


def register_shortcut(title, url_name):
    if (title, url_name) not in _shortcuts:
        _shortcuts.append((title, url_name))


def shortcuts():
    """[(title, url)] for the registered shortcuts."""
    from django.urls import NoReverseMatch, reverse

    links = []
    for title, url_name in _shortcuts:
        try:
            links.append((title, reverse(url_name)))
        except NoReverseMatch:
            log.exception("Dashboard shortcut %r has no URL %r", title, url_name)
    return links
