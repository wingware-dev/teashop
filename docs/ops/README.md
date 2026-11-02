# Running the server

Everything runs on one Ubuntu 24.04 LTS virtual server: PostgreSQL, the
Django app (gunicorn) and Caddy (HTTPS), as Docker containers defined in
`compose.yaml`.  Cloudflare's free plan sits in front.

```
visitor ─► Cloudflare ─► Caddy :443 ─► web (gunicorn :8000) ─► db (PostgreSQL)
                               │
                               └─ /media/* straight from the uploads volume
```

Related: [backups.md](backups.md), [monitoring.md](monitoring.md),
[ops-agent.md](ops-agent.md) (the agent that checks and updates the server),
[../security/security-policy.md](../security/security-policy.md),
[../security/breach-response.md](../security/breach-response.md).

## Accounts this needs (none exist yet; each needs your go-ahead)

| Service | For | Cost |
|---|---|---|
| VPS: Hetzner, DigitalOcean, Linode/Akamai or Vultr | The server: 2-4 vCPU, 4-8 GB RAM, Ubuntu 24.04 | about $10-30/month |
| Domain registrar + Cloudflare (free plan) | DNS, attack protection, caching | domain about $12-20/year |
| GitHub (private repository) | Code, CI, deploys | free |
| Backblaze B2 | Off-site encrypted backups | about $1-5/month |
| UptimeRobot or Better Stack (free plan) | Uptime alerts | free |
| healthchecks.io (free plan) | Alerts when a backup or restore test fails or doesn't run | free |
| Sentry (free Developer plan) | Error tracking | free |

## First-time setup

Steps marked (you) need your accounts; the rest are commands.

1. **(you) Create the server** at the VPS provider: Ubuntu 24.04 LTS, the
   smallest plan with 4 GB RAM, a region near you, **your SSH public key**
   added at creation (no root password).  Turn on the provider's own
   firewall if it has one, allowing 22, 80 and 443 only.
2. **(you) DNS**: at Cloudflare, add an `A` record (and `AAAA` for IPv6)
   for the shop's domain pointing at the server.  Leave the proxy
   (orange cloud) **off** until step 7, so Caddy can get its certificate.
3. **Harden the server.**  From your computer:
   ```sh
   scp -r deploy/server root@<server>:/root/teashop-setup
   ssh root@<server>
   /root/teashop-setup/harden.sh --admin <your-name>
   ```
   It copies root's SSH key to your new admin account, then turns off
   root and password logins.  **Before closing that session**, check in a
   second terminal that `ssh <your-name>@<server>` and `sudo true` work.
4. **Install the app** (as your admin account):
   ```sh
   sudo /root/teashop-setup/install-app.sh --repo git@github.com:<you>/teashop.git --domain <domain>
   ```
   The first run prints a key: add it on GitHub under the repository's
   Settings > Deploy keys (read-only), and run the command again.  It
   writes `/srv/teashop/.env` with fresh secrets.  **Copy `RESTIC_PASSWORD`
   into your password manager now**: without it the backups are useless.
5. **First deploy and owner login:**
   ```sh
   sudo -u deploy -H /srv/teashop/deploy/deploy.sh
   sudo -u deploy -H docker compose -f /srv/teashop/compose.yaml exec web python manage.py createsuperuser
   ```
   Sign in at `https://<domain>/account/login/` and set up two-factor.
   Store the backup codes in your password manager.  The admin is at
   `https://<domain>/<DJANGO_ADMIN_URL>` (see `.env`).
6. **Backups:** create the B2 bucket and key and fill in `.env`
   ([backups.md](backups.md)), then run a backup and a restore test by hand.
7. **(you) Cloudflare proxy on**: turn the orange cloud on, set SSL/TLS
   mode to **Full (strict)**, and uncomment the Cloudflare block at the top
   of `deploy/caddy/Caddyfile` so the app sees visitors' real addresses.
8. **Automatic deploys from GitHub** (below) and **monitoring**
   ([monitoring.md](monitoring.md)).

## Deploying

Deploys are automatic: push to the `release` branch.

```sh
git push origin main:release
```

GitHub Actions runs the tests, then connects to the server as `deploy`
and runs `deploy/deploy.sh <commit>`, which:

1. builds the image `teashop-web:<commit>`;
2. runs Django's production checks on it with the server's real settings
   (stops here if they fail; nothing changed);
3. **backs up the database** to `backups/predeploy/` (the last 10 are kept);
4. applies database migrations;
5. starts the new version (web and the job worker, which sends the emails
   and runs the daily jobs; see `docs/jobs.md`) and waits until their
   health checks pass;
6. if it doesn't, **starts the previous version again** and fails the
   deploy (you get GitHub's failure email).

Each deploy and rollback, succeeded or failed, is recorded in the audit
log and shows under "Operations" on the owner dashboard
(`deploy/record-ops-event.sh`, which runs `manage.py record_ops_event`).

You can run the same script by hand on the server as the `deploy` user.

**Once, after the first deploy with the job worker:** the 6pm order
summary and the renewal reminders used to be systemd timers.  Re-run
`sudo /srv/teashop/deploy/server/install-app.sh --repo ... --domain ...`
to remove them; until then the summary can arrive twice.

### Setting up automatic deploys

1. On your computer: `ssh-keygen -t ed25519 -N "" -f teashop-ci -C github-actions`
2. Copy `teashop-ci.pub` to the server and run
   `sudo /srv/teashop/deploy/server/install-app.sh --repo ... --domain ... --ci-key-file teashop-ci.pub`.
   That key can only run `deploy <commit>` (`deploy/server/ssh-deploy-command.sh`).
3. On GitHub, repository Settings > Secrets and variables > Actions:
   - secret `DEPLOY_HOST`: the server's address
   - secret `DEPLOY_SSH_KEY`: the contents of `teashop-ci` (then delete the file)
   - secret `DEPLOY_KNOWN_HOSTS`: the output of `ssh-keyscan -t ed25519 <server>`
   - variable `SITE_URL`: `https://<domain>` (checked after each deploy)
4. Settings > Environments > `production`: optionally require your
   approval before each deploy.

## Rolling back

On the server, as `deploy`, in `/srv/teashop`:

| Situation | Command |
|---|---|
| New version misbehaves, data is fine | `deploy/rollback.sh` (previous build) |
| A specific older build | `deploy/rollback.sh <commit>` (last 5 builds are kept) |
| The deploy's migrations damaged data | `deploy/rollback.sh --restore-db` right after the bad deploy |
| Restore an older pre-deploy backup | `deploy/rollback.sh --restore-db --dump backups/predeploy/<file> <commit>` |

`--restore-db` replaces the live database with the backup taken just
before the deploy, so **orders placed since then are lost**; it asks
first, and keeps a copy of the database as it was.  Then fix the problem
and deploy again by pushing to `release`.

Migrations should keep the previous version working (add columns before
using them, remove them a release later), so that plain rollbacks are
enough.

## Server upkeep

- **The ops agent** checks the server every hour and does the daily
  upkeep; it proposes anything larger on owner/ops/ ([ops-agent.md](ops-agent.md)).
- **Security updates install automatically** every day.  When one needs a
  reboot, the server reboots at 04:30 UTC; the containers come back on
  their own (about a minute of downtime).
- **Docker** updates from Docker's repository the same way.
- **Python packages** are pinned with hashes in `requirements.lock`
  (runtime), `requirements-ui.lock` (browser tests) and
  `requirements-ci.lock` (pip-audit); the last two are for CI only.  CI
  runs `pip-audit` on all three on every push and weekly; when it reports
  a vulnerability, upgrade on your computer, test, and deploy:
  ```sh
  uv pip compile requirements.txt --python-version 3.13 --generate-hashes --upgrade -o requirements.lock
  uv pip compile requirements-ui.txt -c requirements.lock --python-version 3.13 --generate-hashes --upgrade -o requirements-ui.lock
  uv pip compile requirements-ci.txt -c requirements.lock -c requirements-ui.lock --python-version 3.13 --generate-hashes --upgrade -o requirements-ci.lock
  ```
  Rebuild them in that order (the `-c` keeps any package the locks share,
  such as `certifi`, at the same version).
- **Base images** (Python, PostgreSQL, Caddy): Dependabot opens weekly
  pull requests.
- **Ubuntu release upgrades** (24.04 to 26.04) are not automatic: plan one
  around 2027-2028, or move to a fresh server with a restored backup.

## HTTPS

Caddy gets and renews the Let's Encrypt certificate itself.  Django sets
HSTS for one day at first (`DJANGO_SECURE_HSTS_SECONDS=86400`).  After a
few weeks without HTTPS problems, raise it to a year (31536000) in `.env`
and redeploy.  Including subdomains and joining the browser preload list
are hard to undo; decide on them only once every subdomain serves HTTPS.

## What the hardening script sets up

| Protection | How |
|---|---|
| Automatic security updates | `unattended-upgrades`, reboot at 04:30 UTC when needed |
| SSH | Keys only; no root login; only your admin account, `deploy` and `teashop-ops`; 3 tries per connection |
| Ops agent | `teashop-ops`: no sudo group, no Docker; its key runs only a few fixed commands (health, logs, security updates, log rotation), from the server itself ([ops-agent.md](ops-agent.md)) |
| Brute-force blocking | fail2ban bans an address after 5 failed SSH logins in 10 minutes, for 1 hour, longer for repeat offenders; the app locks a username + address after 5 failed sign-ins for 1 hour |
| Firewall | ufw: only 22 (rate-limited), 80 and 443 in |
| Least privilege | The app runs as an unprivileged user in its container; the database has no open port |
| Log rotation | Docker logs 5 × 10 MB per container; system journal capped at 500 MB |

Docker publishes ports past ufw.  `compose.yaml` publishes only Caddy's
80 and 443; **never add a `ports:` entry for the database or the app**.

The `deploy` account can run Docker, which is equivalent to root on this
server.  Only the CI key (limited to `deploy <commit>`) and your admin
account can log in as it.
