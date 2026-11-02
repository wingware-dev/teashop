"""How the ops agent reaches the server: link() gives the configured one.

- SSHServer ("ssh", on the server): the job worker connects to the
  server's limited teashop-ops account, whose key can run only
  deploy/server/ops/ops-command.py's verbs; each answers with one JSON
  object.  The host key is checked against the known_hosts file
  install-ops-account.sh wrote, so a stranger cannot pose as the server.
- DemoServer ("demo"): made-up readings, to see the pages on a laptop.
- None (OPS_SERVER empty): checks are off.

The web app never connects; only the worker's jobs do.
"""

import json
import logging
import os
import subprocess
import time
from copy import deepcopy

from django.conf import settings

log = logging.getLogger(__name__)

VERBS = ("health", "logs", "apply-security-updates", "rotate-logs")
TIMEOUTS = {"health": 120, "logs": 300, "apply-security-updates": 2100, "rotate-logs": 900}


class ServerError(Exception):
    """The server could not be reached, or refused or failed the command."""


class SSHServer:
    def __init__(self, host=None, user=None, key_dir=None):
        self.host = host or settings.OPS_SSH_HOST
        self.user = user or settings.OPS_SSH_USER
        self.key_dir = key_dir or settings.OPS_SSH_DIR

    def command(self, verb):
        key = os.path.join(self.key_dir, "id_ed25519")
        known_hosts = os.path.join(self.key_dir, "known_hosts")
        return ["ssh", "-F", "/dev/null", "-i", key, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
                "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={known_hosts}",
                "-o", "ConnectTimeout=15", "-o", "LogLevel=ERROR", "-T", f"{self.user}@{self.host}", verb]

    def run(self, verb):
        if verb not in VERBS:
            raise ValueError(f"Not an ops verb: {verb!r}")
        try:
            done = subprocess.run(self.command(verb), capture_output=True, text=True, timeout=TIMEOUTS[verb])
        except subprocess.TimeoutExpired as error:
            raise ServerError(f"{verb}: no answer from the server in {TIMEOUTS[verb]} seconds") from error
        except OSError as error:
            raise ServerError(f"{verb}: could not start ssh ({error})") from error
        try:
            answer = json.loads(done.stdout)
        except ValueError:
            answer = None
        if done.returncode != 0 or not isinstance(answer, dict) or "error" in answer:
            detail = " ".join((done.stderr or done.stdout or "").split())[:300]
            raise ServerError(f"{verb}: the server answered with status {done.returncode}: {detail}")
        return answer


GIB = 1024


def _demo_health():
    now = int(time.time())
    return {
        "taken_at": now, "hostname": "teashop-demo", "cpus": 2, "uptime_seconds": 9 * 86400,
        "os": {"name": "Ubuntu 24.04.3 LTS", "id": "ubuntu", "version": "24.04"},
        "load": [0.31, 0.24, 0.2],
        "memory": {"total_mb": 4 * GIB, "available_mb": 2600, "swap_total_mb": 2 * GIB, "swap_used_mb": 40},
        "disks": [{"mount": "/", "size_gb": 80.0, "free_gb": 9.5, "used_percent": 88.1}],
        "updates": {"pending": 7, "security": 2, "last_automatic_run": now - 3 * 86400,
                    "lists_updated": now - 3 * 86400},
        "reboot_required": {"since": now - 4 * 86400, "packages": ["linux-image-6.8.0-88-generic"]},
        "failed_units": [],
        "containers": [{"name": f"teashop-{name}-1", "status": "Up 4 days (healthy)", "state": "healthy"}
                       for name in ("web", "worker", "db")] +
                      [{"name": "teashop-caddy-1", "status": "Up 4 days", "state": "running"}],
        "containers_error": "",
        "fail2ban": {"banned_now": 3, "banned_total": 41, "failed_now": 1},
        "journal_mb": 420.0,
    }


def _demo_logs():
    return {
        "taken_at": int(time.time()), "hours": 24, "unreadable": {},
        "sources": {
            "ssh": {"logins": [{"user": "owner", "from": "203.0.113.7", "method": "publickey", "count": 2}],
                    "failed_attempts": 212},
            "upgrades": {"recent": ["Packages that will be upgraded: libssl3t64 openssl"], "errors": 0},
            "web": {"lines": 5120, "errors": 1,
                    "samples": ["ERROR django.request: Internal Server Error: /cart/"]},
            "worker": {"lines": 900, "errors": 0, "samples": []},
            "caddy": {"requests": 4800, "server_errors": 1, "client_errors": 96, "samples": ["500 POST /cart/"]},
            "db": {"lines": 40, "errors": 0, "samples": []},
        },
    }


class DemoServer:
    """Made-up readings that change as the agent acts, like a real server."""

    def __init__(self):
        self.state = _demo_health()

    def run(self, verb):
        if verb not in VERBS:
            raise ValueError(f"Not an ops verb: {verb!r}")
        if verb == "health":
            return deepcopy(self.state)
        if verb == "logs":
            return _demo_logs()
        if verb == "apply-security-updates":
            before = dict(self.state["updates"])
            self.state["updates"].update(pending=before["pending"] - before["security"], security=0,
                                         last_automatic_run=int(time.time()))
            return {"ok": True, "exit_status": 0, "before": before, "after": dict(self.state["updates"]),
                    "reboot_required": self.state["reboot_required"],
                    "output": ["Packages that will be upgraded: libssl3t64 openssl", "All upgrades installed"]}
        before = self.state["journal_mb"]
        self.state["journal_mb"] = 180.0
        disk = self.state["disks"][0]
        disks_before = [dict(disk)]
        disk.update(free_gb=disk["free_gb"] + 0.2, used_percent=round(disk["used_percent"] - 0.3, 1))
        return {"ok": True, "exit_status": 0, "journal_mb_before": before, "journal_mb_after": 180.0,
                "disks_before": disks_before, "disks_after": [dict(disk)], "output": ["Vacuuming done"]}


def link():
    """The configured server link, or None when checks are off."""
    if settings.OPS_SERVER == "ssh":
        return SSHServer()
    if settings.OPS_SERVER == "demo":
        return DemoServer()
    return None
