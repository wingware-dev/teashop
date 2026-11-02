# Background jobs

`apps/jobs` keeps a queue of jobs in the database (the `jobs_job` table)
and the **worker** runs them: `python manage.py run_jobs`, the `worker`
service in `compose.yaml`, built from the same image as `web`.  There is
no Redis or other service to run.  It gives every app:

- **queued work**: a request or webhook queues a job and answers at once;
- **automatic retries**: a job that raises runs again later, with longer
  waits each time;
- **schedules**: daily (at a time in a time zone) or periodic jobs, in
  place of systemd timers.

What runs on it now: every email in `apps/checkout/emails.py` and
`apps/fulfillment/emails.py`, the 6pm order summary
(`apps/fulfillment/jobs.py`), the renewal reminders
(`apps/checkout/jobs.py`) and a nightly purge of old job rows.

## Declaring and queueing a job

```python
from datetime import timedelta

from apps import jobs


@jobs.job(max_attempts=8)
def send_reorder_reminder(item_id, note=""):
    item = Item.objects.filter(pk=item_id).first()
    if item is None:
        return                      # gone: nothing to do, don't retry
    ...


send_reorder_reminder.enqueue(item.pk, note="Assam")            # as soon as possible
jobs.enqueue(send_reorder_reminder, item.pk, delay=timedelta(hours=2))
jobs.enqueue(send_reorder_reminder, item.pk, run_at=tomorrow_9am)
jobs.enqueue(send_reorder_reminder, item.pk, key=f"reorder:{item.pk}")
```

- `@jobs.job` or `@jobs.job(max_attempts=5, retry_delay=timedelta(minutes=1))`
  on a **module-level function**.  The job's name is its dotted path
  (`apps.inventory.emails.send_reorder_reminder`), stored with each queued
  job: renaming or moving the function strands the jobs already queued
  (they fail and show on the dashboard).
- **Arguments are JSON**: numbers, strings, lists, dicts, None.  Pass a
  model instance as its pk and fetch it in the job; a Decimal as a
  string; a date as `isoformat()`.  For "any model", `apps.checkout.emails`
  has `ref(obj)` / `deref(value)`.
- `enqueue()` returns the `Job` row.  `run_at` or `delay`: not before
  then.  `key`: while a job with the same key is waiting or running,
  `enqueue()` returns that one instead of queueing a second (one reminder
  per subscription period, one digest per day).
- **Queueing is transactional.**  Inside `transaction.atomic()` the worker
  sees the job only when the transaction commits, and never if it rolls
  back, so a job never runs for an order that was not saved.
- Calling the function directly (`send_reorder_reminder(item.pk)`) runs it
  now, in this process, without the queue.

## Retries

A job runs inside `transaction.atomic()`.  If it raises, its database
changes are rolled back and it is queued again, after 1 minute, then 4,
16, 64 minutes, 4h16m, then every 6 hours, until `max_attempts` runs in
all (default 5; emails use 8, about 18 hours).  `raise jobs.Retry("busy",
delay=timedelta(minutes=10))` asks for another try after a set wait (it
counts as an attempt).  Each failed attempt is logged with its traceback.

After the last attempt the job is **failed**: logged as an error,
recorded in the audit log (`jobs.failed`), and listed on the owner
dashboard ("Background jobs that failed").  The owner fixes the cause and
uses **Run again** on the job (admin → Background jobs), which gives it a
fresh set of attempts.

Because a job may run more than once, make it safe to repeat: do the
outside thing (an email, a label purchase, an API call) last, record that
it happened in the same job (`order.confirmation_sent_at = ...`), and
check that record first when sending twice would hurt.  A job whose
object is gone should return, not raise.

What a job records in the audit log is credited to whoever queued it (the
signed-in owner, an agent, a customer's request), as if it ran then.

## Schedules (daily and periodic jobs)

Declare them in the app's `jobs.py`, which `apps.jobs` imports at startup:

```python
# apps/<app>/jobs.py
from datetime import timedelta

from apps import jobs


@jobs.job(max_attempts=8)
def owner_reminder():
    ...


jobs.schedule(owner_reminder, daily_at="08:00")                 # settings.TIME_ZONE (New York)
jobs.schedule(owner_reminder, daily_at="14:00", tz="UTC")
jobs.schedule(poll_carrier, every=timedelta(minutes=15))
```

- A scheduled job takes no arguments.  It is queued with
  `key="schedule:<name>"`, so a slow run is not doubled.
- The first run is the first time due **after** the worker first sees the
  schedule, never at once.  A run missed while the worker was down
  happens once when it is back (like systemd's `Persistent=true`).
  Changing the time takes effect from the next run.
- A schedule that queues many jobs (one email per customer) should
  `enqueue()` each with a `key`, so each email retries on its own.
- `python manage.py run_jobs --schedules` lists them with their next run;
  so does admin → Background jobs → Schedules.

Don't add systemd timers for app work; they stay only for backups, which
run outside the app containers.

## Emails

`apps/checkout/emails.py` and `apps/fulfillment/emails.py` show the
pattern for an email.  The public function keeps a plain signature and
queues; the job fetches the objects, renders and sends, then marks it
sent:

```python
def order_confirmation(order):                      # callers use this
    return send_order_confirmation.enqueue(order.pk)


@jobs.job(max_attempts=EMAIL_ATTEMPTS)
def send_order_confirmation(order_id):
    if not (order := _order(order_id)):
        return
    send_now(subject, "order_confirmation", context, order.email, order)
    order.confirmation_sent_at = timezone.now()
    order.save(update_fields=["confirmation_sent_at"])
```

`send_now(subject, template, context, to, obj, app="checkout")` renders
`<app>/email/<template>.txt` with the shop's name, contact email and
postal address, sends it, records `<app>.email_sent`, and raises if the
mail server refuses, which makes the job retry.  The public functions
return the `Job` (or False when no email is due), not whether it was
delivered: code that needs to know reads the "sent at" field the job
sets, and the dashboard flags what stays unsent.

## Running it

- **Server:** the `worker` service, started and restarted by
  `deploy/deploy.sh` and `deploy/rollback.sh` with `web`.  Its healthcheck
  reads a heartbeat file the worker touches every few seconds.  `docker
  compose logs worker` shows each job that fails.  `docker compose stop
  worker` lets the job running now finish (60 seconds' grace).  If jobs
  wait more than 10 minutes, the dashboard says the worker is not
  running.
- **Laptop and tests:** `JOBS_EAGER` is on unless `DJANGO_ENV=production`:
  a job due now runs as soon as it is queued, in the same process, through
  the same code as the worker, so emails land in the console or
  `mail.outbox` at once.  A failure there stays queued for retry; set
  `JOBS_EAGER=false` and run `python manage.py run_jobs` to see the worker
  as on the server, or `run_jobs --once` to run what is due and exit.
- **Testing a job's retries:** `@override_settings(JOBS_EAGER=False)`, queue
  it, then `jobs.run_due(now=...)` runs what is due at that time (see
  `apps/jobs/tests/test_queue.py`).
- A worker that dies mid-job leaves it "running"; after
  `JOBS_STALE_AFTER` (30 minutes) another worker runs it again.  Several
  workers can run side by side (`SELECT ... FOR UPDATE SKIP LOCKED`), but
  one is plenty for this shop.
- Finished jobs are deleted after 14 days, failed ones after 90; the audit
  log keeps the record.  Job rows are left out of the audit log
  (`AUDIT_EXCLUDED_MODELS`), as their arguments can hold sign-in links.
- Rolling back to a build from before the job queue stops the worker:
  those builds send their emails themselves.  Jobs still queued wait until
  a build with the worker is deployed again.
