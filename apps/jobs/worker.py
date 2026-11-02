"""The worker loop behind manage.py run_jobs: queue scheduled jobs when
due, run due jobs one at a time, sleep when there are none."""

import logging
import signal
import threading
from pathlib import Path

from django.conf import settings
from django.db import DatabaseError, close_old_connections

from . import queue

log = logging.getLogger(__name__)


class Worker:
    def __init__(self, poll_seconds=None, heartbeat_file=None):
        self.poll_seconds = poll_seconds if poll_seconds is not None else settings.JOBS_POLL_SECONDS
        self.heartbeat_file = Path(heartbeat_file or settings.JOBS_HEARTBEAT_FILE)
        self.stopping = threading.Event()

    def stop(self, *_):
        """Finish the job running now, then return from run()."""
        log.info("Stopping after the current job")
        self.stopping.set()

    def handle_signals(self):
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

    def heartbeat(self):
        """Touch the file compose.yaml's healthcheck looks at."""
        try:
            self.heartbeat_file.touch()
        except OSError:
            log.warning("Could not touch the heartbeat file %s", self.heartbeat_file, exc_info=True)

    def step(self):
        """One round: the schedules, then one job.  Returns whether a job ran."""
        close_old_connections()
        queue.tick()
        return queue.run_next() is not None

    def run(self, once=False):
        """Run until stop() (or, with once, until no job is due)."""
        log.info("Job worker %s started; %d schedule(s)", queue.WORKER_ID, len(queue.schedules()))
        while not self.stopping.is_set():
            self.heartbeat()
            try:
                ran = self.step()
            except DatabaseError:
                # The database restarting, say: wait and try again.
                log.exception("The job worker could not reach the database")
                close_old_connections()
                ran = False
                if once:
                    raise
            if once and not ran:
                break
            if not ran:
                self.stopping.wait(self.poll_seconds)
        log.info("Job worker %s stopped", queue.WORKER_ID)
