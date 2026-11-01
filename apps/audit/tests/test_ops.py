from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from apps.audit.models import AuditEvent
from apps.audit.ops import ops_status, record_ops_event
from apps.core.testing import login_verified, make_owner


def clock_at(when):
    """Move the clock ops_status() reads, and nothing else's (sessions)."""
    return mock.patch("apps.audit.ops.timezone", mock.Mock(now=mock.Mock(return_value=when)))


def status_of(kind):
    return next(status for status in ops_status() if status.kind.name == kind)


class RecordOpsEventCommandTests(TestCase):
    def test_records_system_event_with_details(self):
        out = StringIO()
        call_command(
            "record_ops_event", "deploy", "succeeded",
            "--commit", "0123abcd4567",
            "--message", "Deployed 0123abcd4567\n  (replacing 89abcdef0123)",
            "--detail", "previous=89abcdef0123",
            stdout=out,
        )
        event = AuditEvent.objects.get(action="ops.deploy_succeeded")
        self.assertEqual(event.actor_type, "system")
        self.assertEqual(event.actor_label, "deploy script")
        self.assertEqual(event.object_type, "ops.deploy")
        self.assertEqual(event.object_id, "0123abcd4567")
        self.assertEqual(event.message, "Deployed 0123abcd4567 (replacing 89abcdef0123)")
        self.assertEqual(event.changes, {"previous": "89abcdef0123", "commit": "0123abcd4567"})
        self.assertIn(f"Recorded audit event {event.pk}", out.getvalue())

    def test_default_message(self):
        call_command("record_ops_event", "restore_test", "failed", stdout=StringIO())
        event = AuditEvent.objects.get()
        self.assertEqual(event.action, "ops.restore_test_failed")
        self.assertEqual(event.message, "Restore test failed")
        self.assertEqual(event.actor_label, "restore test")

    def test_rejects_unknown_kind_outcome_and_bad_detail(self):
        for args in (["backups", "succeeded"], ["backup", "passed"], ["backup", "failed", "--detail", "novalue"]):
            with self.subTest(args=args), self.assertRaises(CommandError):
                call_command("record_ops_event", *args, stdout=StringIO(), stderr=StringIO())
        self.assertFalse(AuditEvent.objects.exists())

    def test_function_rejects_unknown_kind(self):
        with self.assertRaises(ValueError):
            record_ops_event("nightly", "succeeded")


class OpsStatusTests(TestCase):
    def age(self, event, days):
        # Audit events are append-only; move the clock instead of the row.
        return clock_at(event.timestamp + timedelta(days=days))

    def test_never_run_is_not_a_problem(self):
        for status in ops_status():
            self.assertIsNone(status.last)
            self.assertFalse(status.needs_attention)

    def test_failure_after_success(self):
        ok = record_ops_event("backup", "succeeded")
        bad = record_ops_event("backup", "failed", message="restic: repository locked")
        status = status_of("backup")
        self.assertEqual(status.last, bad)
        self.assertEqual(status.last_success, ok)
        self.assertTrue(status.failed)
        self.assertTrue(status.needs_attention)

    def test_success_after_failure_clears_it(self):
        record_ops_event("deploy", "failed")
        ok = record_ops_event("deploy", "succeeded")
        status = status_of("deploy")
        self.assertEqual(status.last, ok)
        self.assertFalse(status.needs_attention)

    def test_old_backup_is_overdue_but_old_deploy_is_not(self):
        backup = record_ops_event("backup", "succeeded")
        record_ops_event("deploy", "succeeded")
        with self.age(backup, 1):
            self.assertFalse(status_of("backup").overdue)
        with self.age(backup, 3):
            self.assertTrue(status_of("backup").overdue)
            self.assertFalse(status_of("deploy").overdue)

    def test_only_failures_is_overdue(self):
        record_ops_event("restore_test", "failed")
        self.assertTrue(status_of("restore_test").overdue)


class DashboardOpsTests(TestCase):
    url = reverse("core:owner_dashboard")

    def setUp(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)

    def test_shows_operations_and_nothing_waiting(self):
        record_ops_event("deploy", "succeeded", message="Deployed 0123abcd4567 (replacing nothing)")
        response = self.client.get(self.url)
        self.assertContains(response, "<h2>Operations</h2>", html=True)
        self.assertContains(response, "Deployed 0123abcd4567 (replacing nothing)")
        self.assertContains(response, "None recorded")  # backup, rollback, restore test
        self.assertContains(response, "Nothing is waiting for you.")

    def test_failed_backup_needs_attention(self):
        record_ops_event("backup", "succeeded")
        record_ops_event("backup", "failed", message="Backup failed (exit status 1): Fatal: unable to open repository")
        response = self.client.get(self.url)
        self.assertNotContains(response, "Nothing is waiting for you.")
        self.assertContains(response, "Off-site backup failed")
        self.assertContains(response, "Fatal: unable to open repository")
        self.assertContains(response, "Last succeeded")

    def test_overdue_backup_needs_attention(self):
        event = record_ops_event("backup", "succeeded")
        with clock_at(event.timestamp + timedelta(days=3)):
            response = self.client.get(self.url)
        self.assertContains(response, "Off-site backup is overdue")
        self.assertContains(response, "Overdue")
