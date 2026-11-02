"""The "Needs your attention" queue's deadlines and the reminder emails."""

from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core import attention
from apps.core.attention import Attention, Deadline
from apps.core.models import AttentionRecord
from apps.core.testing import login_verified, make_owner
from apps.reports import reminders

from .helpers import at

EMAIL = dict(OWNER_NOTIFY_EMAIL="owner@example.com", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")


class DeadlineTests(TestCase):
    def test_parse_and_describe(self):
        self.assertEqual(Deadline.parse("0").after, timedelta(0))
        self.assertEqual(Deadline.parse("4h").after, timedelta(hours=4))
        self.assertEqual(Deadline.parse("30m").after, timedelta(minutes=30))
        self.assertEqual(Deadline.parse("3d").describe(), "Reminder after 3 days")
        self.assertEqual(Deadline.parse("0").describe(), "Reminder at once")
        self.assertEqual(Deadline.parse("1h").describe(), "Reminder after 1 hour")
        self.assertEqual(Deadline.parse("18:00").describe(), "Reminder each day at 6 pm")
        with override_settings(ATTENTION_DAILY_AT="08:30"):
            self.assertEqual(Deadline.parse("daily").describe(), "Reminder each day at 8:30 am")
        with self.assertRaises(ValueError):
            Deadline.parse("soon")

    def test_daily_deadline_is_the_next_time_of_day(self):
        six = Deadline.parse("18:00")
        self.assertEqual(six.due(at(2026, 3, 2, 9)), at(2026, 3, 2, 18))
        self.assertEqual(six.due(at(2026, 3, 2, 19)), at(2026, 3, 3, 18))

    def test_the_users_starting_deadlines(self):
        self.assertEqual(attention.deadline_for("support").after, timedelta(0))
        self.assertEqual(attention.deadline_for("orders").at.hour, 18)
        self.assertEqual(attention.deadline_for("posts").after, timedelta(hours=1))
        self.assertEqual(attention.deadline_for("unknown"), attention.deadline_for("other"))
        with override_settings(ATTENTION_DEADLINES={"refunds": "2h"}):
            self.assertEqual(attention.deadline_for("refunds").after, timedelta(hours=2))


def providing(*items):
    return mock.patch.object(attention, "_providers", [lambda: list(items)])


class QueueTests(TestCase):
    def test_first_seen_is_kept_and_gone_items_forget_their_clock(self):
        start = timezone.now()
        item = Attention("Refund order 12", kind="refunds", key="r:12")
        with providing(item):
            [entry] = attention.queue(start)
            self.assertFalse(entry.overdue)
            self.assertEqual(entry.due, start + timedelta(hours=4))
            [later] = attention.queue(start + timedelta(hours=5))
        self.assertEqual(later.since, start)
        self.assertTrue(later.overdue)
        with providing():
            self.assertEqual(attention.queue(start + timedelta(hours=6)), [])
        self.assertFalse(AttentionRecord.objects.exists())

    def test_the_providers_since_counts_and_titles_follow_the_key(self):
        now = timezone.now()
        with providing(Attention("Draft PO 1", kind="approvals", key="po:1", since=now - timedelta(days=4))):
            [entry] = attention.queue(now)
        self.assertTrue(entry.overdue)
        with providing(Attention("Low stock: 2 items", kind="stock", key="low")):
            attention.queue(now)
        with providing(Attention("Low stock: 3 items", kind="stock", key="low")):
            [entry] = attention.queue(now + timedelta(hours=1))
        self.assertEqual(entry.since, now)
        self.assertEqual(AttentionRecord.objects.get(key="low").title, "Low stock: 3 items")

    def test_overdue_first_then_grouped_by_kind(self):
        now = timezone.now()
        items = [Attention("Stock low", kind="stock", key="s"),
                 Attention("Support: angry customer", kind="support", key="t"),
                 Attention("Backup failed", kind="jobs", key="b", level="urgent")]
        with providing(*items):
            entries = attention.queue(now)
        self.assertEqual(entries[0].item.key, "t")  # due at once
        groups = attention.grouped(entries)
        self.assertEqual([kind.name for kind, _deadline, _entries in groups], ["support", "jobs", "stock"])


@override_settings(**EMAIL)
class ReminderTests(TestCase):
    def test_overdue_items_are_emailed_once(self):
        now = timezone.now()
        items = [Attention("Customer asks for a refund", kind="support", key="sup:1", url="/owner/x/"),
                 Attention("Stock low", kind="stock", key="s"),
                 Attention("Orders to pack: 2", kind="orders", key="o", since=now - timedelta(days=2))]
        with providing(*items):
            sent = reminders.overdue(now)
            self.assertEqual([e.item.key for e in sent], ["sup:1"])
            self.assertEqual(reminders.overdue(now + timedelta(minutes=5)), [])
        [email] = mail.outbox
        self.assertEqual(email.to, ["owner@example.com"])
        self.assertIn("Customer asks for a refund", email.subject)
        self.assertIn("http://testserver/owner/x/", email.body.replace("localhost:8000", "testserver"))
        self.assertIn("Support escalations (reminder at once)", email.body)
        self.assertIsNotNone(AttentionRecord.objects.get(key="sup:1").reminded_at)

    def test_daily_lists_everything_and_marks_overdue(self):
        now = timezone.now()
        items = [Attention("Reorder: 2 items with no purchase order yet", kind="stock", key="reorder"),
                 Attention("Purchase order for Leaf Co waits for your approval", kind="purchase_orders",
                           key="po:3", since=now - timedelta(days=2))]
        with providing(*items):
            entries = reminders.daily(now)
        self.assertEqual(len(entries), 2)
        [email] = mail.outbox
        self.assertIn("2 things waiting, 1 overdue", email.subject)
        self.assertIn("OVERDUE: Purchase order for Leaf Co", email.body)
        self.assertIn("Reorder: 2 items", email.body)

    def test_nothing_waiting_sends_nothing(self):
        with providing():
            self.assertEqual(reminders.daily(), [])
            self.assertEqual(reminders.overdue(), [])
        self.assertEqual(mail.outbox, [])

    @override_settings(OWNER_NOTIFY_EMAIL="")
    def test_no_owner_email_sends_nothing(self):
        with providing(Attention("x", kind="support")):
            self.assertEqual(reminders.overdue(), [])

    def test_a_failed_send_raises_and_is_not_marked(self):
        with providing(Attention("x", kind="support", key="k")), \
                mock.patch("apps.reports.reminders.send_now", side_effect=OSError("refused")):
            with self.assertRaises(OSError):
                reminders.overdue()
        self.assertIsNone(AttentionRecord.objects.get(key="k").reminded_at)

    def test_jobs_are_scheduled(self):
        from apps.jobs.queue import schedules

        names = {s.name for s in schedules()}
        self.assertTrue({"apps.reports.jobs.overdue_reminders", "apps.reports.jobs.daily_reminder",
                         "apps.reports.jobs.accounting_summary"} <= names)


class DashboardTests(TestCase):
    def test_grouped_by_kind_with_deadlines_and_ops_items(self):
        from apps.audit.ops import record_ops_event

        record_ops_event("backup", "failed", message="Fatal: unable to open repository")
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        with mock.patch.object(attention, "_providers", [*attention._providers,
                                                         lambda: [Attention("Angry customer", kind="support")]]):
            page = self.client.get(reverse("core:owner_dashboard"))
        self.assertContains(page, "Support escalations")
        self.assertContains(page, "Reminder at once")
        self.assertContains(page, "Failed jobs and backups")
        self.assertContains(page, "Off-site backup failed")
        self.assertContains(page, "Overdue:")
