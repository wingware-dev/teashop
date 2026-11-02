# The ops agent (`apps/ops`)

The ops agent looks after the server for you: it checks the server's
health every hour, does the routine upkeep every morning (security
updates, logs), and writes what it found and did on the dashboard.
Anything larger it **proposes**, with steps you can follow; it cannot do
those itself.

Where to see it: the owner dashboard's **Operations** card ("Server health
check", "Server upkeep") and **Needs your attention** list, and the server
page, **owner/ops/** (Shortcuts: "Server health and security").

## What it can and cannot do

The agent works through a limited account on the server, `teashop-ops`,
which can run only these, and nothing else:

| Command | What it does | Needs root? |
|---|---|---|
| `health` | Load, memory, disks, updates waiting, restart needed, failed services, the app's containers, blocked addresses, journal size | Partly (containers, fail2ban, journal size) |
| `logs` | The last day's logs, summarised: SSH logins, update runs, errors from the app, the job worker, Caddy and PostgreSQL | Yes (read only) |
| `apply-security-updates` | Refresh the package lists and run `unattended-upgrade`: security updates only, as the daily automatic run does | Yes |
| `rotate-logs` | `logrotate`, then trim the system journal to 400 MB | Yes |

It **cannot**: restart the server, install other updates, change any
setting, read the shop's database or `.env`, run Docker, add users or
keys, or open ports.  Those come to you as proposals.

How that is enforced, outside the agent's own code:

- The app's job worker connects over SSH with a key that, in
  `~teashop-ops/.ssh/authorized_keys`, may run only
  `/usr/local/sbin/teashop-ops-command` (`deploy/server/ops/ops-command.py`),
  only from the server's own private networks, with no terminal or
  forwarding.  That file belongs to root, so the account cannot widen it.
- `teashop-ops` is not in the `sudo` or `docker` groups.  sudo lets it run
  `/usr/local/sbin/teashop-ops-helper` (`deploy/server/ops/ops-helper.sh`)
  with exactly the arguments listed in `/etc/sudoers.d/91-teashop-ops`.
  The helper's commands are fixed: nothing the caller passes reaches a
  shell or another program's options.
- The worker checks the server's host key (`/etc/teashop/ops-agent/known_hosts`),
  so nothing else can pose as the server.  The web app never connects.
- Every run, action and proposal is in the audit log, credited to
  `ops-agent`.

If the key leaked, the worst anyone could do with it is read the health
summary and logs, install security updates and rotate logs, and only from
the server itself.

## Setting it up

New servers get it from `harden.sh` and `install-app.sh` (docs/ops/README.md);
nothing more to do.  For a server set up before phase 11, as your admin
account:

```sh
cd /srv/teashop && sudo -u deploy git pull     # or wait for the next deploy
sudo /srv/teashop/deploy/server/install-app.sh --repo <repo> --domain <domain>
```

That creates the account, its sudo rules and key, adds it to SSH's
`AllowUsers`, and sets `OPS_SERVER=ssh` in `.env`.  The next deploy starts
the checks.  Re-run `install-app.sh` after a deploy that changes
`deploy/server/ops/` to install the new commands (they are copies owned
by root, so a deploy alone cannot change what the agent may do).

To check it by hand:

```sh
sudo -u deploy -H docker compose -f /srv/teashop/compose.yaml exec worker \
    ssh -F /dev/null -i /run/ops-agent/id_ed25519 -o UserKnownHostsFile=/run/ops-agent/known_hosts \
    teashop-ops@host.docker.internal health
```

Settings (`.env`): `OPS_SERVER` (`ssh` on the server, `demo` for made-up
readings on a laptop, empty for off), `OPS_HEALTH_EVERY_MINUTES` (60),
`OPS_UPKEEP_AT` (05:30, New York time), `OPS_SSH_HOST` and `OPS_SSH_USER`
(defaults fit `compose.yaml`).

## The hourly health check

No AI.  It reads `health`, applies the rules in `apps/ops/findings.py` and
keeps the reading (`ServerReport`, kept 90 days):

| Finding | When | Level |
|---|---|---|
| A container (web, worker, db, caddy) missing, stopped or unhealthy | | urgent |
| Disk full | 85% (warning), 95% (urgent) | |
| Short of memory | under 10% free, or over half the swap used | warning |
| Very busy | 5-minute load over twice the processors | warning |
| Security updates waiting | and the automatic run is over 2 days old (else information) | warning |
| Automatic updates stopped | no run for 2 days | warning |
| Restart waiting | over 2 days (the automatic one at 04:30 UTC should have done it) | warning |
| System services failed | any | warning |
| Ubuntu support ending | within a year (warning), 60 days (urgent) | |

Urgent findings go on the attention list as "Things that are broken"
(reminder after an hour); warnings as "Other" (the daily reminder).
The audit log gets an `ops.health_check_*` event when the result changes,
and once a day otherwise, so the Operations card shows the check is alive.
If the server can't be reached, the check is "failed" there.

## The daily upkeep

Through the agents' tool loop (`apps/agents`, docs/agents.md), with the
agent's tools: read the health again, read the logs, apply security
updates, rotate logs, propose, and report.  The tools refuse an action the
findings don't call for, and each runs at most once a day.  At most three
proposals a day; none that is already waiting, approved, or was declined
in the last 30 days.

Like the other agents it runs on a **free stand-in** (plain rules, no AI
service) unless you name `ops-agent` in `AGENTS_LIVE`.  The stand-in is
enough for this job: its decisions come straight from the findings.  If
the live AI fails or the monthly cap is reached, the stand-in does that
day's upkeep instead.

### Logs are untrusted

Strangers can write into the logs: an SSH login attempt with a made-up
user name, a web address with words in it.  So the agent gets log text
fenced as untrusted, lines that look like instructions are withheld, and
a proposal made after reading logs carries a note telling you to check
each command.  Never run a proposed command you don't understand; ask
someone you trust first.

## Proposals

Each has a reason, numbered steps with the exact commands (run as your
admin account over SSH), and a risk.  On owner/ops/: **Approve** (then
carry it out, and **Mark done**), or **Decline**.  Approving does not
make the agent do anything: you or someone you trust carries out the
steps.

## The quarterly security review

See [../security/quarterly-review.md](../security/quarterly-review.md).
