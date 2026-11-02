"""Ops items for the owner dashboard's "Needs your attention" list: a
deploy, rollback, backup or restore test that failed, or a scheduled one
overdue (ops.py)."""

from apps.core.attention import Attention

from .ops import ops_status


def attention_items():
    items = []
    for status in ops_status():
        if not status.needs_attention:
            continue
        if status.failed:
            title = f"{status.kind.title} failed {status.last.timestamp:%Y-%m-%d %H:%M}"
            detail = status.last.message[:200] if status.last.message else ""
            if status.last_success:
                detail += f"  Last succeeded {status.last_success.timestamp:%Y-%m-%d %H:%M}."
            since = status.last.timestamp
        else:
            last = status.last_success.timestamp if status.last_success else None
            title = f"{status.kind.title} is overdue: last succeeded {last:%Y-%m-%d %H:%M}" if last else \
                f"{status.kind.title} is overdue: never succeeded"
            detail = "Its timer may have stopped: see docs/ops/backups.md."
            since = (last + status.kind.expected_every) if last else status.last.timestamp
        items.append(Attention(title, detail.strip(), "", "urgent", kind="jobs",
                               key=f"ops:{status.kind.name}", since=since))
    return items
