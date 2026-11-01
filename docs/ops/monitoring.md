# Monitoring, errors and logs

## Uptime

`https://<domain>/healthz` answers `{"status": "ok", ...}` with status 200
when the app is running and can reach its database, and 503 otherwise.
It also shows which commit is deployed.

Point a free uptime monitor at it (UptimeRobot, Better Stack or similar;
needs an account): check every 5 minutes, alert by email (and by app push
if you like) after 2 failures.  Add a second monitor for the home page.

Docker checks the same URL every 30 seconds inside the server; `docker
compose ps` shows `healthy` or `unhealthy`.

## Backups

healthchecks.io pings from the backup and restore-test jobs alert you when
one fails or doesn't run ([backups.md](backups.md)).

## Errors

The app reports unhandled errors to Sentry when `SENTRY_DSN` is set in
`.env` (Sentry's free Developer plan is enough; needs an account).  It
sends no personal data (`send_default_pii` is off) and tags each error
with the deployed commit.  Without a DSN, errors only go to the log.

## Logs

All containers log to Docker, which keeps 5 files of 10 MB each per
container and deletes older ones.  The system journal is capped at 500 MB.

```sh
cd /srv/teashop
docker compose logs --tail 100 web          # the app, including each request
docker compose logs --since 1h caddy        # HTTPS front end (JSON lines)
docker compose logs db
journalctl -u ssh --since today             # SSH logins
sudo fail2ban-client status sshd            # banned addresses
journalctl -u unattended-upgrades --since -7d
```

## Who did what

The audit log (owner dashboard, and the admin under "Audit log") records
every change to the shop's data, every sign-in and failed sign-in, and the
actions of AI agents, with time, account and address.
