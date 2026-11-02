"""The job queue: declaring jobs, queueing them, running them, retries and
schedules.  The public names are re-exported by apps.jobs; see
docs/jobs.md for how apps use them.
"""

import dataclasses
import logging
import os
import socket
import traceback
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from apps.audit import Actor, acting_as, current_actor, record
from apps.audit.context import SYSTEM

from .models import Job, Schedule

log = logging.getLogger(__name__)

# Waits after failed attempts 1, 2, 3...: 1 minute, 4, 16, 64, then 4h16m,
# then at most MAX_RETRY_DELAY.
DEFAULT_RETRY_DELAY = timedelta(minutes=1)
RETRY_FACTOR = 4
MAX_RETRY_DELAY = timedelta(hours=6)

_jobs = {}        # name -> JobFunction
_schedules = {}   # name -> Periodic


class Retry(Exception):
    """Raise from a job to try it again later (after delay, else the usual
    backoff).  Counts as an attempt."""

    def __init__(self, message="", delay=None):
        super().__init__(message)
        self.delay = delay


class JobFunction:
    """A function declared with @job: call it to run it now, or call
    .enqueue() to have the worker run it."""

    def __init__(self, fn, max_attempts, retry_delay):
        self.fn = fn
        self.name = f"{fn.__module__}.{fn.__qualname__}"
        self.max_attempts = max_attempts
        self.retry_delay = retry_delay
        self.__doc__ = fn.__doc__
        self.__name__ = fn.__name__
        self.__module__ = fn.__module__
        self.__qualname__ = fn.__qualname__

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def __repr__(self):
        return f"<job {self.name}>"

    def enqueue(self, *args, **kwargs):
        """Queue a run with these arguments, as soon as possible."""
        return enqueue(self, *args, **kwargs)

    def delay_after(self, attempt):
        """How long to wait after failed attempt number attempt (1, 2...)."""
        return min(self.retry_delay * RETRY_FACTOR ** (attempt - 1), MAX_RETRY_DELAY)


def job(fn=None, *, max_attempts=5, retry_delay=DEFAULT_RETRY_DELAY):
    """Declare a job function: @job, or @job(max_attempts=8).

    Its arguments must be JSON values (pass model instances as their pk);
    the worker imports it by its dotted path, so it must be a module-level
    function.  It runs in a transaction; if it raises, the transaction is
    rolled back and it is tried again later, up to max_attempts runs in
    all.  Anything it does outside the database (an email, an API call)
    may therefore happen again: do that last, or check first."""
    def declare(fn):
        declared = JobFunction(fn, max_attempts, retry_delay)
        _jobs[declared.name] = declared
        return declared
    return declare(fn) if fn is not None else declare


def enqueue(job_function, *args, run_at=None, delay=None, key="", **kwargs):
    """Queue job_function(*args, **kwargs) and return its Job.

    run_at or delay: not before then.  key: if a job with this key is
    waiting or running, return that one instead of queueing another.
    Inside a transaction, the worker sees the job only once it commits, and
    never if it rolls back.  With settings.JOBS_EAGER (development and
    tests) a job due now runs at once, in this process."""
    if not isinstance(job_function, JobFunction):
        raise TypeError(f"{job_function!r} is not declared with @jobs.job")
    if key:
        pending = Job.objects.filter(key=key, status__in=[Job.Status.QUEUED, Job.Status.RUNNING]).first()
        if pending:
            return pending
    now = timezone.now()
    if run_at is None:
        run_at = now + delay if delay else now
    queued = Job.objects.create(name=job_function.name, args=list(args), kwargs=kwargs, key=key, run_at=run_at,
                                max_attempts=job_function.max_attempts, actor=_actor_to_json(_job_actor()))
    if settings.JOBS_EAGER and run_at <= now:
        _run(queued, job_function)
    return queued


# -- Schedules ---------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class Periodic:
    name: str
    job: JobFunction
    daily_at: time | None
    every: timedelta | None
    tz: str

    @property
    def spec(self):
        if self.daily_at:
            return f"daily at {self.daily_at:%H:%M} {self.tz}"
        return f"every {int(self.every.total_seconds())}s"

    def next_after(self, moment):
        """The first run time after moment."""
        if self.every:
            return moment + self.every
        zone = ZoneInfo(self.tz)
        local = moment.astimezone(zone)
        candidate = datetime.combine(local.date(), self.daily_at, tzinfo=zone)
        if candidate <= local:
            candidate = datetime.combine(local.date() + timedelta(days=1), self.daily_at, tzinfo=zone)
        return candidate


def schedule(job_function, *, daily_at=None, every=None, tz=None, name=None):
    """Run job_function (no arguments) periodically: daily_at "HH:MM" in
    time zone tz (default settings.TIME_ZONE), or every timedelta.

    Declare schedules at import time of the app's jobs.py, which
    apps.jobs imports at startup.  A run missed while the worker was down
    happens once when it is back, like a systemd timer with
    Persistent=true.  The first run is the first time due after the
    schedule is first seen, never at once."""
    if not isinstance(job_function, JobFunction):
        raise TypeError(f"{job_function!r} is not declared with @jobs.job")
    if (daily_at is None) == (every is None):
        raise ValueError("Give daily_at or every")
    if isinstance(daily_at, str):
        daily_at = time.fromisoformat(daily_at)
    if every is not None and every <= timedelta(0):
        raise ValueError("every must be positive")
    entry = Periodic(name or job_function.name, job_function, daily_at, every, tz or settings.TIME_ZONE)
    _schedules[entry.name] = entry
    return entry


def schedules():
    return sorted(_schedules.values(), key=lambda entry: entry.name)


def tick(now=None):
    """Queue the scheduled jobs that are due.  Returns the Jobs queued."""
    now = now or timezone.now()
    queued = []
    for entry in schedules():
        try:
            with transaction.atomic():
                row = Schedule.objects.select_for_update().filter(name=entry.name).first()
                if row is None:
                    Schedule.objects.create(name=entry.name, spec=entry.spec, next_run_at=entry.next_after(now))
                    continue
                if row.spec != entry.spec:
                    row.spec, row.next_run_at = entry.spec, entry.next_after(now)
                    row.save(update_fields=["spec", "next_run_at"])
                    continue
                if row.next_run_at > now:
                    continue
                queued.append(enqueue(entry.job, key=f"schedule:{entry.name}"))
                row.last_run_at, row.next_run_at = now, entry.next_after(now)
                row.save(update_fields=["last_run_at", "next_run_at"])
        except IntegrityError:
            # Another worker created the row first; it handles this round.
            log.info("Schedule %s was created by another worker", entry.name)
    return queued


# -- Running -----------------------------------------------------------------

WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


def claim(now=None):
    """Take the next due job (or one whose worker died) and mark it
    running.  Returns the Job or None."""
    now = now or timezone.now()
    stale = now - settings.JOBS_STALE_AFTER
    with transaction.atomic():
        due = (Job.objects.select_for_update(skip_locked=True)
               .filter(status=Job.Status.QUEUED, run_at__lte=now).order_by("run_at", "pk").first())
        if due is None:
            due = (Job.objects.select_for_update(skip_locked=True)
                   .filter(status=Job.Status.RUNNING, started_at__lt=stale).order_by("started_at", "pk").first())
            if due is not None:
                log.warning("Job %s was left running by %s; running it again", due, due.locked_by)
        if due is None:
            return None
        due.status, due.started_at, due.locked_by = Job.Status.RUNNING, now, WORKER_ID
        due.attempts += 1
        due.save(update_fields=["status", "started_at", "locked_by", "attempts"])
    return due


def run_next(now=None):
    """Claim and run one due job.  Returns it, or None if none was due."""
    claimed = claim(now)
    if claimed is None:
        return None
    if claimed.attempts > claimed.max_attempts:
        # Its last attempt was left running by a worker that died.
        claimed.attempts = claimed.max_attempts
        _finish(claimed, RuntimeError("The worker running its last attempt stopped"))
    else:
        _finish(claimed, _call(claimed))
    return claimed


def run_due(now=None, limit=1000):
    """Run due jobs until none is left (tests, run_jobs --once).  Returns
    how many ran."""
    count = 0
    while count < limit and run_next(now) is not None:
        count += 1
    return count


def _run(queued, job_function):
    """Run a job just queued (eager mode), as the worker would."""
    queued.status, queued.started_at, queued.locked_by = Job.Status.RUNNING, timezone.now(), "eager"
    queued.attempts += 1
    queued.save(update_fields=["status", "started_at", "locked_by", "attempts"])
    _finish(queued, _call(queued, job_function))


def _call(running, job_function=None):
    """Run the job's function; returns the exception it raised, or None."""
    try:
        job_function = job_function or resolve(running.name)
        with acting_as(_actor_from_json(running.actor)), transaction.atomic():
            job_function.fn(*running.args, **running.kwargs)
    except Exception as exc:  # any failure is retried and logged below
        return exc
    return None


def _finish(running, exc):
    now = timezone.now()
    if exc is None:
        running.status, running.finished_at = Job.Status.DONE, now
        running.save(update_fields=["status", "finished_at"])
        return
    running.last_error = "".join(traceback.format_exception(exc))[-4000:]
    job_function = _jobs.get(running.name)
    if running.attempts < running.max_attempts and job_function is not None:
        wait = getattr(exc, "delay", None) if isinstance(exc, Retry) else None
        wait = wait or job_function.delay_after(running.attempts)
        running.status, running.run_at = Job.Status.QUEUED, now + wait
        log.warning("Job %s failed (attempt %d of %d), trying again at %s: %s", running, running.attempts,
                    running.max_attempts, running.run_at.isoformat(timespec="seconds"), exc,
                    exc_info=not isinstance(exc, Retry))
    else:
        running.status, running.finished_at = Job.Status.FAILED, now
        log.error("Job %s failed for good after %d attempt(s)", running, running.attempts, exc_info=exc)
        with acting_as(_actor_from_json(running.actor)):
            record("jobs.failed", object_type="jobs.job", object_id=str(running.pk), object_repr=str(running),
                   message=f"Gave up after {running.attempts} attempt(s): {exc}"[:500])
    running.save(update_fields=["status", "run_at", "finished_at", "last_error", "attempts"])


def resolve(name):
    """The JobFunction for a job name, importing its module if needed."""
    if name not in _jobs:
        found = import_string(name)
        if not isinstance(found, JobFunction):
            raise TypeError(f"{name} is not declared with @jobs.job")
    return _jobs[name]


def retry_now(queryset):
    """Queue failed jobs again with a fresh set of attempts (the owner's
    "Run again" action).  Returns how many."""
    return queryset.filter(status=Job.Status.FAILED).update(
        status=Job.Status.QUEUED, attempts=0, run_at=timezone.now(), finished_at=None)


def _job_actor():
    """Who a job queued now runs as: whoever queued it, except that a job
    an AI agent queues (an email, a reminder) runs later as the system,
    since the agent did not decide on it."""
    actor = current_actor()
    return SYSTEM if actor.type == "agent" else actor


def _actor_to_json(actor):
    return dataclasses.asdict(actor)


def _actor_from_json(data):
    try:
        return Actor(**data) if data else current_actor()
    except TypeError:
        log.warning("Unreadable actor %r on a job; running it as the system", data)
        return current_actor()


# -- Housekeeping ------------------------------------------------------------

@job
def purge():
    """Delete finished jobs: done ones after JOBS_KEEP_DONE, failed ones
    after JOBS_KEEP_FAILED (the audit log keeps the record)."""
    now = timezone.now()
    done, _ = Job.objects.filter(status=Job.Status.DONE, finished_at__lt=now - settings.JOBS_KEEP_DONE).delete()
    failed, _ = Job.objects.filter(status=Job.Status.FAILED,
                                   finished_at__lt=now - settings.JOBS_KEEP_FAILED).delete()
    if done or failed:
        log.info("Purged %d done and %d failed jobs", done, failed)


schedule(purge, daily_at="04:30")
