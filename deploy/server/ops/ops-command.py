#!/usr/bin/env python3
"""What the ops agent may do on the server: the SSH forced command for its key.

Installed as /usr/local/sbin/teashop-ops-command by install-ops-account.sh,
which puts this in ~teashop-ops/.ssh/authorized_keys (owned by root, so the
account cannot change it):

    command="/usr/local/sbin/teashop-ops-command",restrict,from="<private ranges>" ssh-ed25519 AAAA... teashop-ops-agent

Whatever the client asks to run, SSH runs this instead, as the unprivileged
teashop-ops account (no Docker, no general sudo).  It accepts one verb and
prints one JSON object:

    health                   load, memory, disks, updates waiting, reboot needed,
                             failed services, containers, banned addresses
    logs                     the last day's logs, summarised: SSH logins, update
                             runs, app and web server errors
    apply-security-updates   install the waiting security updates now
                             (what the daily automatic run would do)
    rotate-logs              rotate log files and trim the system journal

Anything that needs root goes through /usr/local/sbin/teashop-ops-helper,
which sudo lets this account run with exactly the arguments listed in
/etc/sudoers.d/91-teashop-ops and nothing else.  Anything larger (a
reboot, a release upgrade, a bigger disk) is not here: the agent proposes
it to the owner.

Log lines hold text from outside (SSH user names, web addresses), so the
app treats this command's "logs" output as untrusted.

Standard library only; runs on the server's own Python 3 (Ubuntu 24.04:
3.12).  The TEASHOP_OPS_* variables are for the tests; SSH does not pass
a client's variables through (no AcceptEnv for them).
"""

import json
import os
import re
import subprocess
import sys
import time

ROOT = os.environ.get("TEASHOP_OPS_ROOT", "/")
HELPER = os.environ.get("TEASHOP_OPS_HELPER", "/usr/local/sbin/teashop-ops-helper")
VERBS = ("health", "logs", "apply-security-updates", "rotate-logs")
LOG_SOURCES = ("ssh", "upgrades", "web", "worker", "caddy", "db")
SAMPLE_LINES = 8
LINE_CHARS = 300


def path(*parts):
    return os.path.join(ROOT, *[part.lstrip("/") for part in parts])


def read(*parts, default=""):
    try:
        with open(path(*parts), encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return default


def mtime(*parts):
    try:
        return int(os.path.getmtime(path(*parts)))
    except OSError:
        return None


def run(args, timeout=60):
    """(exit status, stdout, stderr); status 127 if the program is missing."""
    try:
        done = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=timeout)
    except FileNotFoundError:
        return 127, "", f"{args[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "", f"{args[0]}: timed out after {timeout}s"
    return done.returncode, done.stdout, done.stderr


def helper(*args, timeout=60):
    """Run the root helper through sudo (-n: never ask for a password)."""
    return run(["sudo", "-n", HELPER, *args], timeout=timeout)


# --- Parsers (kept apart from the I/O so the tests can feed them text) -------

def parse_os_release(text):
    values = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key.strip()] = value.strip().strip('"')
    return {"name": values.get("PRETTY_NAME", ""), "id": values.get("ID", ""),
            "version": values.get("VERSION_ID", "")}


def parse_meminfo(text):
    kib = {}
    for line in text.splitlines():
        match = re.match(r"(\w+):\s+(\d+)", line)
        if match:
            kib[match[1]] = int(match[2])
    return {"total_mb": kib.get("MemTotal", 0) // 1024, "available_mb": kib.get("MemAvailable", 0) // 1024,
            "swap_total_mb": kib.get("SwapTotal", 0) // 1024,
            "swap_used_mb": (kib.get("SwapTotal", 0) - kib.get("SwapFree", 0)) // 1024}


def parse_apt_check(text):
    """update-notifier's apt-check prints "<updates>;<security updates>"."""
    match = re.search(r"(\d+);(\d+)", text)
    return {"pending": int(match[1]), "security": int(match[2])} if match else None


def parse_apt_list(text):
    """`apt list --upgradable`: one line per package; security ones come
    from the -security pocket."""
    lines = [line for line in text.splitlines() if "/" in line and "[upgradable" in line]
    return {"pending": len(lines), "security": sum(1 for line in lines if "-security" in line.split()[0])}


def parse_containers(text):
    containers = []
    for line in text.splitlines():
        name, _, status = line.partition("\t")
        if name.strip():
            state = "healthy" if "(healthy)" in status else "unhealthy" if "(unhealthy)" in status else \
                "starting" if "(health: starting)" in status else "running" if status.startswith("Up") else "stopped"
            containers.append({"name": name.strip(), "status": status.strip(), "state": state})
    return containers


def parse_fail2ban(text):
    def number(label):
        match = re.search(label + r":\s*(\d+)", text)
        return int(match[1]) if match else None

    return {"banned_now": number("Currently banned"), "banned_total": number("Total banned"),
            "failed_now": number("Currently failed")}


def parse_size_mb(text):
    """"... take up 120.5M in the file system." -> 120.5"""
    match = re.search(r"(\d+(?:\.\d+)?)\s*([KMGT])", text)
    if not match:
        return None
    return round(float(match[1]) * {"K": 1 / 1024, "M": 1, "G": 1024, "T": 1024 * 1024}[match[2]], 1)


def clip(line):
    line = " ".join(line.split())
    return line if len(line) <= LINE_CHARS else line[:LINE_CHARS] + "..."


ACCEPTED_RE = re.compile(r"Accepted (\w+) for (\S+) from (\S+)")
FAILED_SSH_RE = re.compile(r"Failed \w+ for|Invalid user|authentication failure|"
                           r"Connection closed by (authenticating|invalid) user|maximum authentication attempts")


def summarise_ssh(text):
    logins = {}
    failed = 0
    for line in text.splitlines():
        match = ACCEPTED_RE.search(line)
        if match:
            key = (match[2], match[3], match[1])
            logins[key] = logins.get(key, 0) + 1
        elif FAILED_SSH_RE.search(line):
            failed += 1
    return {"logins": [{"user": user, "from": address, "method": method, "count": count}
                       for (user, address, method), count in sorted(logins.items())],
            "failed_attempts": failed}


ERROR_RE = re.compile(r"\b(ERROR|CRITICAL|FATAL|PANIC|Traceback)\b")


def summarise_errors(text):
    lines = [line for line in text.splitlines() if ERROR_RE.search(line)]
    return {"lines": len(text.splitlines()), "errors": len(lines), "samples": [clip(line) for line in lines[-SAMPLE_LINES:]]}


def summarise_caddy(text):
    """Caddy logs one JSON object per request."""
    server_errors, client_errors, requests, samples = 0, 0, 0, []
    for line in text.splitlines():
        try:
            entry = json.loads(line[line.index("{"):])
        except ValueError:
            continue
        status = entry.get("status")
        if not isinstance(status, int):
            continue
        requests += 1
        if status >= 500:
            server_errors += 1
            request = entry.get("request") or {}
            samples.append(clip(f"{status} {request.get('method', '')} {request.get('uri', '')}"))
        elif status >= 400:
            client_errors += 1
    return {"requests": requests, "server_errors": server_errors, "client_errors": client_errors,
            "samples": samples[-SAMPLE_LINES:]}


def summarise_upgrades(text):
    lines = [line for line in text.splitlines() if line.strip()]
    return {"recent": [clip(line) for line in lines[-SAMPLE_LINES:]],
            "errors": sum(1 for line in lines if "ERROR" in line or "WARNING" in line)}


# --- Verbs --------------------------------------------------------------------

def disks():
    found, devices = [], set()
    for mount in ("/", "/var/lib/docker", "/srv"):
        try:
            stat = os.statvfs(path(mount))
            device = os.stat(path(mount)).st_dev
        except OSError:
            continue
        if device in devices:
            continue
        devices.add(device)
        size = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = size - stat.f_bfree * stat.f_frsize
        found.append({"mount": mount, "size_gb": round(size / 1e9, 1), "free_gb": round(free / 1e9, 1),
                      "used_percent": round(100 * used / (used + free), 1) if used + free else 0})
    return found


def updates():
    status, out, err = run([path("/usr/lib/update-notifier/apt-check")])
    counts = parse_apt_check(err + out) if status == 0 else None
    if counts is None:
        status, out, _ = run(["apt", "list", "--upgradable"])
        counts = parse_apt_list(out) if status == 0 else {"pending": None, "security": None}
    counts["last_automatic_run"] = mtime("/var/lib/apt/periodic/unattended-upgrades-stamp")
    counts["lists_updated"] = mtime("/var/lib/apt/periodic/update-success-stamp")
    return counts


def reboot_required():
    since = mtime("/var/run/reboot-required")
    if since is None:
        return None
    packages = sorted(set(read("/var/run/reboot-required.pkgs").split()))
    return {"since": since, "packages": packages}


def health():
    uptime = read("/proc/uptime").split()
    load = read("/proc/loadavg").split()
    status, out, _ = run(["systemctl", "list-units", "--state=failed", "--no-legend", "--plain"])
    failed = [line.split()[0] for line in out.splitlines() if line.strip()] if status == 0 else None
    c_status, c_out, c_err = helper("containers")
    f_status, f_out, _ = helper("fail2ban")
    j_status, j_out, j_err = helper("journal-usage")
    return {
        "taken_at": int(time.time()),
        "hostname": read("/etc/hostname").strip(),
        "os": parse_os_release(read("/etc/os-release")),
        "uptime_seconds": int(float(uptime[0])) if uptime else None,
        "load": [float(value) for value in load[:3]] if len(load) >= 3 else None,
        "cpus": os.cpu_count(),
        "memory": parse_meminfo(read("/proc/meminfo")),
        "disks": disks(),
        "updates": updates(),
        "reboot_required": reboot_required(),
        "failed_units": failed,
        "containers": parse_containers(c_out) if c_status == 0 else None,
        "containers_error": "" if c_status == 0 else clip(c_err),
        "fail2ban": parse_fail2ban(f_out) if f_status == 0 else None,
        "journal_mb": parse_size_mb(j_out + j_err) if j_status == 0 else None,
    }


def logs():
    sources, problems = {}, {}
    for source in LOG_SOURCES:
        status, out, err = helper("logs", source, timeout=120)
        if status != 0:
            problems[source] = clip(err or f"exit status {status}")
            continue
        if source == "ssh":
            sources[source] = summarise_ssh(out)
        elif source == "upgrades":
            sources[source] = summarise_upgrades(out)
        elif source == "caddy":
            sources[source] = summarise_caddy(out)
        else:
            sources[source] = summarise_errors(out)
    return {"taken_at": int(time.time()), "hours": 24, "sources": sources, "unreadable": problems}


def apply_security_updates():
    before = updates()
    status, out, err = helper("apply-security-updates", timeout=1800)
    after = updates()
    tail = [clip(line) for line in (out + err).splitlines() if line.strip()][-20:]
    return {"ok": status == 0, "exit_status": status, "before": before, "after": after,
            "reboot_required": reboot_required(), "output": tail}


def rotate_logs():
    _, before, before_err = helper("journal-usage")
    disks_before = disks()
    status, out, err = helper("rotate-logs", timeout=600)
    _, after, after_err = helper("journal-usage")
    return {"ok": status == 0, "exit_status": status,
            "journal_mb_before": parse_size_mb(before + before_err), "journal_mb_after": parse_size_mb(after + after_err),
            "disks_before": disks_before, "disks_after": disks(),
            "output": [clip(line) for line in (out + err).splitlines() if line.strip()][-10:]}


ACTIONS = {"health": health, "logs": logs, "apply-security-updates": apply_security_updates,
           "rotate-logs": rotate_logs}


def log_to_syslog(message):
    run(["logger", "-t", "teashop-ops", message[:300]], timeout=10)


def main(request):
    verb = request.strip()
    if verb not in ACTIONS or request != verb:
        print(json.dumps({"error": "refused", "allowed": list(VERBS)}))
        print("refused: allowed are " + ", ".join(VERBS), file=sys.stderr)
        log_to_syslog(f"refused ops command: {request[:200]!r}")
        return 2
    log_to_syslog(f"ops agent ran {verb}")
    print(json.dumps(ACTIONS[verb](), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(os.environ.get("SSH_ORIGINAL_COMMAND", "")))
