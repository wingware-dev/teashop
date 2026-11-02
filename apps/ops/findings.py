"""What the server's readings mean: assess(health) and assess_logs(logs)
turn the JSON from deploy/server/ops/ops-command.py into Findings.

A finding says how bad it is (urgent, warning, info), in plain words, and
what fixes it:

- fix="apply_security_updates" or "rotate_logs": the agent may do it
  itself, through its limited account;
- proposal=Proposal(...): something larger (a restart, a bigger disk, an
  Ubuntu release upgrade) the agent may only propose; the owner approves
  and carries it out.

Plain rules, no AI: the hourly check uses them, and so does the daily
upkeep's stand-in.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from datetime import timezone as dt_timezone

URGENT, WARNING, INFO = "urgent", "warning", "info"
LEVELS = (URGENT, WARNING, INFO)

DISK_WARNING, DISK_URGENT = 85, 95
MEMORY_LOW_SHARE = 0.10
SWAP_HIGH_SHARE = 0.5
# Automatic updates run daily and restart the server at 04:30 UTC when one
# needs it; older than this means they are not happening.
UPDATES_LATE = timedelta(days=2)
REBOOT_LATE = timedelta(days=2)
JOURNAL_ROTATE_MB = 400
OTHER_UPDATES_PROPOSE = 25
SERVER_ERRORS_WARNING = 20
EXPECTED_CONTAINERS = ("web", "worker", "db", "caddy")
# End of Ubuntu's standard (free) security support for each LTS release.
SUPPORT_ENDS = {"22.04": date(2027, 4, 30), "24.04": date(2029, 5, 31), "26.04": date(2031, 5, 31)}
SUPPORT_PLAN_AHEAD = timedelta(days=365)

ADMIN_SSH = "ssh <your admin name>@<server>"


@dataclass(frozen=True)
class Proposal:
    key: str  # the same while it is the same change ("reboot", "disk:/")
    title: str
    reason: str
    steps: str
    risk: str = "low"  # low, medium, high: what could go wrong doing it


@dataclass(frozen=True)
class Finding:
    level: str
    key: str
    title: str
    detail: str = ""
    fix: str = ""  # an action the agent may take itself
    proposal: Proposal | None = None
    extra: dict = field(default_factory=dict)

    def as_dict(self):
        data = {"level": self.level, "key": self.key, "title": self.title, "detail": self.detail, "fix": self.fix}
        if self.proposal:
            data["proposal"] = self.proposal.__dict__.copy()
        return data


def when(timestamp):
    return datetime.fromtimestamp(timestamp, tz=dt_timezone.utc) if timestamp else None


def ago(timestamp, now):
    moment = when(timestamp)
    if moment is None:
        return "never"
    days = (now - moment).total_seconds() / 86400
    return f"{days:.0f} days ago" if days >= 1.5 else f"{days * 24:.0f} hours ago"


def _disks(health, findings):
    for disk in health.get("disks") or []:
        used = disk.get("used_percent", 0)
        if used < DISK_WARNING:
            continue
        level = URGENT if used >= DISK_URGENT else WARNING
        findings.append(Finding(
            level, f"disk:{disk['mount']}", f"Disk {disk['mount']} is {used:.0f}% full",
            f"{disk.get('free_gb', 0):.1f} GB free of {disk.get('size_gb', 0):.0f} GB.  When it fills, the database "
            "stops taking orders.", fix="rotate_logs",
            proposal=Proposal(
                f"disk:{disk['mount']}", f"Make room on the server's disk ({disk['mount']} is {used:.0f}% full)",
                f"The disk has {disk.get('free_gb', 0):.1f} GB free of {disk.get('size_gb', 0):.0f} GB after rotating "
                "the logs.  The shop's data and builds keep growing.",
                "1. At your VPS provider, resize the server's disk to the next size up (most providers do it in a few "
                "minutes; some need the server off for it).\n"
                f"2. Or look at what takes the room: {ADMIN_SSH}, then\n"
                "   sudo du -xh --max-depth=2 /srv /var/lib/docker | sort -h | tail\n"
                "   Old pre-deploy database backups in /srv/teashop/backups/predeploy can go (the newest 10 are kept "
                "automatically).", "low")))


def _memory(health, findings):
    memory = health.get("memory") or {}
    total, available = memory.get("total_mb") or 0, memory.get("available_mb") or 0
    swap_total, swap_used = memory.get("swap_total_mb") or 0, memory.get("swap_used_mb") or 0
    low = total and available < total * MEMORY_LOW_SHARE
    swapping = swap_total and swap_used > swap_total * SWAP_HIGH_SHARE
    if low or swapping:
        findings.append(Finding(
            WARNING, "memory", "The server is short of memory",
            f"{available} MB free of {total} MB; swap {swap_used} of {swap_total} MB used.  Pages get slow, and the "
            "system may stop the app to free memory.",
            proposal=Proposal(
                "memory", "Move the server to a plan with more memory",
                f"Only {available} MB of {total} MB memory was free, with {swap_used} MB in swap.",
                "1. At your VPS provider, resize the server to the plan with the next amount of memory (it restarts "
                "the server: about a minute of downtime; choose a quiet hour).\n"
                "2. Nothing else changes: the containers start again by themselves.", "low")))
    load = health.get("load") or []
    cpus = health.get("cpus") or 1
    if len(load) >= 2 and load[1] > 2 * cpus:
        findings.append(Finding(WARNING, "load", "The server is very busy",
                                f"Load {load[1]:.1f} over 5 minutes on {cpus} processors."))


def _updates(health, findings, now):
    updates = health.get("updates") or {}
    security, pending = updates.get("security"), updates.get("pending")
    last = when(updates.get("last_automatic_run"))
    late = last is None or now - last > UPDATES_LATE
    if security is None:
        findings.append(Finding(WARNING, "updates:unknown", "Could not read which updates are waiting"))
    elif security:
        findings.append(Finding(
            WARNING if late else INFO, "updates:security", f"{security} security update{'s' if security != 1 else ''} "
            "waiting", f"Automatic updates last ran {ago(updates.get('last_automatic_run'), now)}.",
            fix="apply_security_updates"))
    elif late:
        findings.append(Finding(
            WARNING, "updates:late", "Automatic updates have not run lately",
            f"They last ran {ago(updates.get('last_automatic_run'), now)}; they should run every day.",
            proposal=Proposal(
                "updates:late", "Check why automatic updates stopped",
                f"The daily automatic security updates last ran {ago(updates.get('last_automatic_run'), now)}.",
                f"1. {ADMIN_SSH}\n2. systemctl status unattended-upgrades apt-daily-upgrade.timer\n"
                "3. sudo unattended-upgrade --dry-run -v   (shows what blocks it)\n"
                "4. If a timer is off: sudo systemctl enable --now apt-daily.timer apt-daily-upgrade.timer", "low")))
    other = (pending or 0) - (security or 0)
    if other >= OTHER_UPDATES_PROPOSE:
        findings.append(Finding(
            INFO, "updates:other", f"{other} other (non-security) updates waiting",
            "Automatic updates install only security fixes.",
            proposal=Proposal(
                "updates:other", f"Install the {other} other updates waiting on the server",
                "Automatic updates install only security fixes; bug-fix updates pile up.  Installing them now and "
                "then keeps the next release upgrade small.",
                f"1. Right after a backup has run: {ADMIN_SSH}\n2. sudo apt-get update && sudo apt-get upgrade\n"
                "3. If it says a restart is needed: sudo reboot   (about a minute of downtime)", "medium")))


def _reboot(health, findings, now):
    reboot = health.get("reboot_required")
    if not reboot:
        return
    since = when(reboot.get("since"))
    packages = ", ".join(reboot.get("packages") or []) or "an update"
    if since and now - since > REBOOT_LATE:
        findings.append(Finding(
            WARNING, "reboot", f"A restart has been waiting since {since:%Y-%m-%d}",
            f"For {packages}.  The automatic restart at 04:30 UTC should have done it.",
            proposal=Proposal(
                "reboot", "Restart the server to finish installing updates",
                f"{packages} needs a restart to take effect, waiting since {since:%Y-%m-%d}; the automatic "
                "restart at 04:30 UTC did not happen.",
                f"1. At a quiet hour: {ADMIN_SSH}\n2. sudo reboot\n"
                "3. About a minute later the shop is back by itself; the dashboard's next health check confirms it.\n"
                "4. If the automatic restart keeps not happening: "
                "grep -i reboot /etc/apt/apt.conf.d/52teashop-unattended-upgrades", "low")))
    else:
        findings.append(Finding(INFO, "reboot", "A restart is waiting for tonight's automatic one",
                                f"For {packages}."))


def _services(health, findings):
    failed = health.get("failed_units")
    if failed:
        names = ", ".join(failed[:6])
        findings.append(Finding(
            WARNING, "units:" + ",".join(sorted(failed))[:120], f"System services failed: {names}",
            proposal=Proposal(
                "units:" + ",".join(sorted(failed))[:120], f"Look at the failed system services ({names})",
                "These services stopped with an error.  Some matter (backups, updates), some don't.",
                f"1. {ADMIN_SSH}\n" + "".join(f"2. systemctl status {name}\n   journalctl -u {name} -n 50\n"
                                              for name in failed[:3]) +
                "3. Once fixed: sudo systemctl reset-failed", "low")))
    containers = health.get("containers")
    if containers is None:
        findings.append(Finding(WARNING, "containers:unknown", "Could not read the app's containers",
                                health.get("containers_error", "")))
        return
    by_service = {}
    for container in containers:
        parts = container["name"].split("-")
        if len(parts) >= 3:
            by_service[parts[-2]] = container
    for service in EXPECTED_CONTAINERS:
        container = by_service.get(service)
        if container is None or container["state"] in ("stopped", "unhealthy"):
            state = "missing" if container is None else container["status"]
            findings.append(Finding(
                URGENT, f"container:{service}", f"The {service} container is not running well ({state})",
                "Docker restarts containers by itself; if it stays like this, see docs/ops/README.md "
                "(Rolling back) or deploy again."))


def _support(health, findings, now):
    os_info = health.get("os") or {}
    ends = SUPPORT_ENDS.get(os_info.get("version", ""))
    if os_info.get("id") != "ubuntu" or ends is None:
        findings.append(Finding(INFO, "os:unknown", f"Unknown system {os_info.get('name') or ''}".strip(),
                                "The agent knows the support dates of Ubuntu 22.04, 24.04 and 26.04."))
        return
    left = ends - now.date()
    if left <= SUPPORT_PLAN_AHEAD:
        level = URGENT if left.days < 60 else WARNING
        findings.append(Finding(
            level, f"os:{os_info['version']}", f"Ubuntu {os_info['version']} security support ends {ends:%B %Y}",
            f"{left.days} days left.",
            proposal=Proposal(
                f"os:{os_info['version']}", f"Move the shop to a newer Ubuntu before {ends:%B %Y}",
                f"Ubuntu {os_info['version']} gets no free security updates after {ends:%B %Y}.",
                "The safe way is a fresh server rather than upgrading in place:\n"
                "1. Create a new server with the newest Ubuntu LTS and run deploy/server/harden.sh and "
                "install-app.sh on it (docs/ops/README.md).\n"
                "2. Restore last night's backup on it (docs/ops/backups.md) and check the shop there.\n"
                "3. Point DNS at the new server, then cancel the old one after a week.", "high")))


def assess(health, now=None):
    """Findings from a "health" reading, worst first."""
    now = now or datetime.now(tz=dt_timezone.utc)
    findings = []
    _services(health, findings)
    _disks(health, findings)
    _memory(health, findings)
    _updates(health, findings, now)
    _reboot(health, findings, now)
    _support(health, findings, now)
    journal = health.get("journal_mb")
    if journal and journal > JOURNAL_ROTATE_MB:
        findings.append(Finding(INFO, "journal", f"The system journal takes {journal:.0f} MB", fix="rotate_logs"))
    return sorted(findings, key=lambda finding: LEVELS.index(finding.level))


def assess_logs(logs):
    """Findings from a "logs" reading.  Log text comes from outside (user
    names, web addresses): findings quote only counts and the fixed fields
    the server parsed, never free text."""
    findings = []
    sources = logs.get("sources") or {}
    ssh = sources.get("ssh") or {}
    logins = ssh.get("logins") or []
    if logins:
        people = "; ".join(f"{login['user']} from {login['from']} ({login['count']})" for login in logins[:8])
        findings.append(Finding(INFO, "ssh:logins", f"SSH logins in the last day: {len(logins)}",
                                f"{people}.  The ops agent logs in as teashop-ops and deploys as deploy; anything "
                                "else you don't recognise needs a look (docs/security/breach-response.md)."))
    if ssh.get("failed_attempts"):
        findings.append(Finding(INFO, "ssh:failed", f"{ssh['failed_attempts']} failed SSH login attempts",
                                "Usual on the internet; fail2ban blocks repeat offenders."))
    caddy = sources.get("caddy") or {}
    if caddy.get("server_errors", 0) >= SERVER_ERRORS_WARNING:
        findings.append(Finding(WARNING, "web:errors", f"{caddy['server_errors']} pages failed with server errors",
                                f"Of {caddy.get('requests', 0)} requests in the last day.  Sentry (if set up) "
                                "has the details."))
    for name in ("web", "worker", "db"):
        errors = (sources.get(name) or {}).get("errors", 0)
        if errors:
            findings.append(Finding(INFO, f"log:{name}", f"{errors} error lines in the {name} log"))
    for name in logs.get("unreadable") or {}:
        findings.append(Finding(INFO, f"log:{name}:unreadable", f"Could not read the {name} log"))
    return sorted(findings, key=lambda finding: LEVELS.index(finding.level))


def summary(findings):
    """One line: the worst findings' titles, or that all is well."""
    serious = [finding for finding in findings if finding.level != INFO]
    if not serious:
        return "All is well"
    titles = "; ".join(finding.title for finding in serious[:3])
    more = len(serious) - 3
    return titles + (f"; and {more} more" if more > 0 else "")
