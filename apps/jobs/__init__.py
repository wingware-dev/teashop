"""Background jobs, kept in PostgreSQL (the jobs_job table) and run by the
worker (manage.py run_jobs, the "worker" service in compose.yaml), so
there is no other service to run.  See docs/jobs.md.

    from apps import jobs

    @jobs.job(max_attempts=8)
    def send_receipt(order_id):
        ...

    send_receipt.enqueue(order.pk)                       # soon
    jobs.enqueue(send_receipt, order.pk, delay=timedelta(hours=1), key=f"receipt:{order.pk}")
    jobs.schedule(send_receipt_digest, daily_at="18:00")  # in the app's jobs.py

A job that raises is tried again later, with growing waits; after its
last attempt it is marked failed, recorded in the audit log and listed on
the owner dashboard, where the owner can run it again.
"""

__all__ = ["Retry", "enqueue", "job", "run_due", "schedule"]


def __getattr__(name):
    # Loaded on first use: Django imports this package before the models
    # are ready, and queue.py needs them.
    if name in __all__:
        from . import queue

        return getattr(queue, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
