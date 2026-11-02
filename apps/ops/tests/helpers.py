"""Test helpers: a server whose readings a test sets, built on the demo one."""

import time
from copy import deepcopy

from apps.ops.server import DemoServer, ServerError


def healthy():
    """A reading with nothing to report."""
    reading = DemoServer().run("health")
    reading["disks"] = [{"mount": "/", "size_gb": 80.0, "free_gb": 60.0, "used_percent": 25.0}]
    reading["updates"] = {"pending": 0, "security": 0, "last_automatic_run": int(time.time()) - 3600,
                          "lists_updated": int(time.time()) - 3600}
    reading["reboot_required"] = None
    reading["journal_mb"] = 100.0
    return reading


class FakeServer(DemoServer):
    """The demo server, with readings to set and failures to inject; keeps
    each verb run in .calls."""

    def __init__(self, health=None, fail=()):
        super().__init__()
        if health is not None:
            self.state = deepcopy(health)
        self.fail = set(fail)
        self.calls = []
        self.logs = None

    def run(self, verb):
        self.calls.append(verb)
        if verb in self.fail:
            raise ServerError(f"{verb}: the server answered with status 255: Connection refused")
        if verb == "logs" and self.logs is not None:
            return deepcopy(self.logs)
        return super().run(verb)
