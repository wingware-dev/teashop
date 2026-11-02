"""The job queue: queueing, running, retries, schedules, the worker and
the dashboard items."""

import smtplib
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from django.core import mail
from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from apps import jobs
from apps.audit import acting_as_agent
from apps.audit.models import AuditEvent
from apps.jobs import alerts, queue
from apps.jobs.models import Job, Schedule
from apps.jobs.worker import Worker

calls = []


@jobs.job
def remember(value, label=""):
    calls.append((value, label))


@jobs.job
def ping():
    calls.append("ping")


@jobs.job(max_attempts=3)
def always_fails():
    calls.append("tried")
    raise RuntimeError("the mail server is down")


@jobs.job(max_attempts=3)
def asks_to_wait():
    raise jobs.Retry("busy", delay=timedelta(minutes=10))


@jobs.job
def writes_then_fails():
    Schedule.objects.create(name="written-by-a-failing-job", spec="x", next_run_at=timezone.now())
    raise RuntimeError("after writing")


@jobs.job
def records_something():
    from apps.audit import record

    record("tests.did_something", message="from a job")


class QueueTestCase(TestCase):
    def setUp(self):
        calls.clear()


@override_settings(JOBS_EAGER=False)
class EnqueueTests(QueueTestCase):
    def test_queued_then_run_by_the_worker(self):
        queued = remember.enqueue(7, label="seven")
        self.assertEqual(queued.status, Job.Status.QUEUED)
        self.assertEqual(queued.name, "apps.jobs.tests.test_queue.remember")
        self.assertEqual(calls, [])
        self.assertEqual(jobs.run_due(), 1)
        self.assertEqual(calls, [(7, "seven")])
        queued.refresh_from_db()
        self.assertEqual(queued.status, Job.Status.DONE)
        self.assertEqual(queued.attempts, 1)
        self.assertEqual(jobs.run_due(), 0)

    def test_rolled_back_transaction_queues_nothing(self):
        with self.assertRaises(ValueError), transaction.atomic():
            remember.enqueue(1)
            raise ValueError("the order failed")
        self.assertFalse(Job.objects.exists())

    def test_not_run_before_its_time(self):
        jobs.enqueue(remember, 1, delay=timedelta(hours=1))
        self.assertEqual(jobs.run_due(), 0)
        self.assertEqual(jobs.run_due(now=timezone.now() + timedelta(hours=1, seconds=1)), 1)
        self.assertEqual(calls, [(1, "")])

    def test_key_keeps_one_pending_job(self):
        first = jobs.enqueue(remember, 1, key="once")
        self.assertEqual(jobs.enqueue(remember, 2, key="once"), first)
        jobs.run_due()
        jobs.enqueue(remember, 3, key="once")  # the first one is done: queue again
        jobs.run_due()
        self.assertEqual(calls, [(1, ""), (3, "")])

    def test_only_declared_jobs(self):
        with self.assertRaises(TypeError):
            jobs.enqueue(print, "hello")

    def test_audit_events_credited_to_whoever_queued_it(self):
        with acting_as_agent("support-agent"):
            records_something.enqueue()
        jobs.run_due()
        event = AuditEvent.objects.get(action="tests.did_something")
        self.assertEqual(event.actor_label, "support-agent")

    def test_job_rows_stay_out_of_the_audit_log(self):
        remember.enqueue(1)
        jobs.run_due()
        self.assertFalse(AuditEvent.objects.filter(object_type__startswith="jobs.").exclude(
            action="jobs.failed").exists())


@override_settings(JOBS_EAGER=False)
class RetryTests(QueueTestCase):
    def test_retried_with_growing_waits_then_failed_and_listed(self):
        queued = always_fails.enqueue()
        start = timezone.now()
        with self.assertLogs("apps.jobs.queue", level="WARNING"):
            jobs.run_due(now=start)
        queued.refresh_from_db()
        self.assertEqual((queued.status, queued.attempts), (Job.Status.QUEUED, 1))
        self.assertIn("the mail server is down", queued.last_error)
        first_wait = queued.run_at - start
        self.assertGreaterEqual(first_wait, timedelta(minutes=1))
        self.assertLess(first_wait, timedelta(minutes=2))
        self.assertEqual(jobs.run_due(now=start + timedelta(seconds=30)), 0)  # not yet

        later = start + timedelta(days=1)
        with self.assertLogs("apps.jobs.queue", level="WARNING"):
            queue.run_next(now=later)
        queued.refresh_from_db()
        self.assertGreaterEqual(queued.run_at - timezone.now(), timedelta(minutes=3, seconds=50))  # 4 minutes
        with self.assertLogs("apps.jobs.queue", level="ERROR") as logs:
            queue.run_next(now=later + timedelta(days=1))
        self.assertIn("failed for good", "\n".join(logs.output))
        queued.refresh_from_db()
        self.assertEqual((queued.status, queued.attempts), (Job.Status.FAILED, 3))
        self.assertEqual(calls, ["tried"] * 3)
        self.assertTrue(AuditEvent.objects.filter(action="jobs.failed", object_id=str(queued.pk)).exists())

        items = alerts.attention_items()
        self.assertEqual([item.title for item in items], ["Background jobs that failed: 1"])
        self.assertIn("test_queue.always_fails", items[0].detail)

        self.assertEqual(queue.retry_now(Job.objects.all()), 1)
        queued.refresh_from_db()
        self.assertEqual((queued.status, queued.attempts), (Job.Status.QUEUED, 0))

    def test_retry_asks_for_its_own_wait(self):
        queued = asks_to_wait.enqueue()
        with self.assertLogs("apps.jobs.queue", level="WARNING"):
            jobs.run_due()
        queued.refresh_from_db()
        self.assertGreater(queued.run_at - timezone.now(), timedelta(minutes=9))

    def test_failed_attempt_rolls_back_its_changes(self):
        writes_then_fails.enqueue()
        with self.assertLogs("apps.jobs.queue", level="WARNING"):
            jobs.run_due()
        self.assertFalse(Schedule.objects.filter(name="written-by-a-failing-job").exists())

    def test_unknown_job_fails_at_once(self):
        Job.objects.create(name="apps.jobs.tests.test_queue.renamed_long_ago")
        with self.assertLogs("apps.jobs.queue", level="ERROR"):
            jobs.run_due()
        self.assertEqual(Job.objects.get().status, Job.Status.FAILED)

    def test_job_left_running_by_a_dead_worker_runs_again(self):
        queued = remember.enqueue(5)
        queue.claim()  # the worker that took it died
        self.assertEqual(jobs.run_due(), 0)
        with self.assertLogs("apps.jobs.queue", level="WARNING"):
            jobs.run_due(now=timezone.now() + timedelta(minutes=31))
        queued.refresh_from_db()
        self.assertEqual((queued.status, queued.attempts), (Job.Status.DONE, 2))
        self.assertEqual(calls, [(5, "")])

    def test_dead_worker_on_the_last_attempt_fails_the_job(self):
        queued = always_fails.enqueue()
        Job.objects.filter(pk=queued.pk).update(attempts=3, status=Job.Status.RUNNING,
                                                started_at=timezone.now() - timedelta(hours=1))
        with self.assertLogs("apps.jobs.queue", level="WARNING"):
            jobs.run_due()
        queued.refresh_from_db()
        self.assertEqual((queued.status, queued.attempts), (Job.Status.FAILED, 3))
        self.assertEqual(calls, [])

    def test_worker_not_running_is_on_the_dashboard(self):
        jobs.enqueue(remember, 1, run_at=timezone.now() - timedelta(minutes=11))
        self.assertEqual([item.title for item in alerts.attention_items()],
                         ["Background jobs are not running: 1 waiting"])
        with override_settings(JOBS_EAGER=True):
            self.assertEqual(alerts.attention_items(), [])


class EagerTests(QueueTestCase):
    @override_settings(JOBS_EAGER=True)
    def test_eager_runs_at_once_through_the_queue(self):
        queued = remember.enqueue(9)
        self.assertEqual(calls, [(9, "")])
        self.assertEqual(Job.objects.get(pk=queued.pk).status, Job.Status.DONE)

    @override_settings(JOBS_EAGER=True)
    def test_eager_failure_stays_queued_and_later_jobs_wait(self):
        with self.assertLogs("apps.jobs.queue", level="WARNING"):
            queued = always_fails.enqueue()
        self.assertEqual(Job.objects.get(pk=queued.pk).status, Job.Status.QUEUED)
        jobs.enqueue(remember, 1, delay=timedelta(hours=1))
        self.assertEqual(calls, ["tried"])


@override_settings(JOBS_EAGER=False)
class ScheduleTests(QueueTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(queue._schedules, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_daily_at_runs_once_a_day_and_catches_up_once(self):
        new_york = ZoneInfo("America/New_York")
        jobs.schedule(ping, daily_at="18:00", tz="America/New_York", name="summary")
        noon = datetime(2026, 11, 2, 12, 0, tzinfo=new_york)
        self.assertEqual(queue.tick(noon), [])  # first seen: not at once
        row = Schedule.objects.get(name="summary")
        self.assertEqual(row.next_run_at, datetime(2026, 11, 2, 18, 0, tzinfo=new_york))
        self.assertEqual(queue.tick(noon + timedelta(hours=5)), [])

        evening = datetime(2026, 11, 2, 18, 0, 5, tzinfo=new_york)
        [queued] = queue.tick(evening)
        self.assertEqual(queued.key, "schedule:summary")
        self.assertEqual(queue.tick(evening + timedelta(minutes=1)), [])
        row.refresh_from_db()
        self.assertEqual(row.next_run_at, datetime(2026, 11, 3, 18, 0, tzinfo=new_york))

        # The worker was down for three days: one run when it is back.
        jobs.run_due(now=evening)
        back = datetime(2026, 11, 6, 9, 0, tzinfo=new_york)
        self.assertEqual(len(queue.tick(back)), 1)
        self.assertEqual(queue.tick(back + timedelta(minutes=1)), [])

    def test_daily_time_follows_daylight_saving(self):
        entry = jobs.schedule(ping, daily_at="18:00", tz="America/New_York", name="dst")
        # Clocks went back on November 1, 2026: 18:00 is 22:00 UTC before, 23:00 after.
        before = entry.next_after(datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo("UTC")))
        after = entry.next_after(datetime(2026, 11, 1, 12, 0, tzinfo=ZoneInfo("UTC")))
        self.assertEqual(before.astimezone(ZoneInfo("UTC")).hour, 22)
        self.assertEqual(after.astimezone(ZoneInfo("UTC")).hour, 23)

    def test_every_and_a_changed_schedule(self):
        jobs.schedule(ping, every=timedelta(minutes=15), name="poll")
        start = timezone.now()
        queue.tick(start)
        self.assertEqual(len(queue.tick(start + timedelta(minutes=15))), 1)
        jobs.schedule(ping, every=timedelta(hours=1), name="poll")
        self.assertEqual(queue.tick(start + timedelta(hours=1)), [])  # the change resets the next run
        self.assertEqual(Schedule.objects.get(name="poll").spec, "every 3600s")

    def test_bad_schedules_are_refused(self):
        with self.assertRaises(ValueError):
            jobs.schedule(ping)
        with self.assertRaises(ValueError):
            jobs.schedule(ping, daily_at="08:00", every=timedelta(hours=1))
        with self.assertRaises(TypeError):
            jobs.schedule(print, daily_at="08:00")


class DeclaredSchedulesTests(TestCase):
    def test_the_apps_daily_jobs_are_scheduled(self):
        specs = {entry.name: entry.spec for entry in queue.schedules()}
        self.assertEqual(specs["apps.fulfillment.jobs.order_summary"], "daily at 18:00 America/New_York")
        self.assertEqual(specs["apps.checkout.jobs.subscription_reminders"], "daily at 14:00 UTC")
        self.assertIn("apps.jobs.queue.purge", specs)

    @override_settings(JOBS_EAGER=False, JOBS_KEEP_DONE=timedelta(days=14), JOBS_KEEP_FAILED=timedelta(days=90))
    def test_purge_keeps_recent_and_waiting_jobs(self):
        old = timezone.now() - timedelta(days=20)
        Job.objects.create(name="a", status=Job.Status.DONE, finished_at=old)
        kept_failed = Job.objects.create(name="b", status=Job.Status.FAILED, finished_at=old)
        waiting = Job.objects.create(name="c", run_at=old)
        queue.purge()
        self.assertEqual(set(Job.objects.values_list("pk", flat=True)), {kept_failed.pk, waiting.pk})


@override_settings(JOBS_EAGER=False)
class WorkerTests(QueueTestCase):
    def test_once_runs_due_jobs_and_touches_the_heartbeat(self):
        remember.enqueue(1)
        remember.enqueue(2)
        with tempfile.TemporaryDirectory() as tmp:
            heartbeat = Path(tmp) / "heartbeat"
            worker = Worker(poll_seconds=0, heartbeat_file=heartbeat)
            with self.assertLogs("apps.jobs.worker", level="INFO"):
                worker.run(once=True)
            self.assertTrue(heartbeat.exists())
        self.assertEqual(calls, [(1, ""), (2, "")])

    def test_stop_ends_the_loop(self):
        worker = Worker(poll_seconds=0, heartbeat_file=Path(tempfile.gettempdir()) / "teashop-test.heartbeat")
        with mock.patch.object(worker, "step", side_effect=lambda: worker.stop() or False), \
                self.assertLogs("apps.jobs.worker", level="INFO"):
            worker.run()


@override_settings(JOBS_EAGER=False, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class QueuedEmailTests(QueueTestCase):
    """The emails keep their signatures and are retried."""

    def test_sign_in_link_is_retried_until_the_mail_server_answers(self):
        from apps.checkout import emails

        queued = emails.sign_in_link("ada@example.com", "https://shop.example/link")
        self.assertEqual(mail.outbox, [])
        with mock.patch("apps.checkout.emails.send_mail", side_effect=smtplib.SMTPServerDisconnected("gone")), \
                self.assertLogs("apps.jobs.queue", level="WARNING"):
            jobs.run_due()
        queued.refresh_from_db()
        self.assertEqual((queued.status, queued.attempts), (Job.Status.QUEUED, 1))
        jobs.run_due(now=timezone.now() + timedelta(minutes=2))
        self.assertEqual(mail.outbox[0].to, ["ada@example.com"])
        self.assertIn("https://shop.example/link", mail.outbox[0].body)
        queued.refresh_from_db()
        self.assertEqual(queued.status, Job.Status.DONE)
