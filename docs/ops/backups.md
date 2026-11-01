# Backups

| What | When | Where | Kept |
|---|---|---|---|
| Database + uploaded files, encrypted (restic) | Daily 03:15 UTC | Backblaze B2 | 7 daily, 5 weekly, 12 monthly |
| Database, before each deploy | Each deploy | Server, `backups/predeploy/` | Last 10 |
| Restore test | 1st of each month, 05:00 UTC | Scratch database on the server | Result on the owner dashboard, in the journal and healthchecks.io |

The backups are encrypted on the server with `RESTIC_PASSWORD` before they
leave it; Backblaze cannot read them.  **Keep `RESTIC_PASSWORD` and the B2
key in your password manager**: if the server is lost, they are all you
need to restore, and without the password the backups cannot be read.

## Setting up Backblaze B2 (needs your account)

1. Create a Backblaze account and a **private** bucket, e.g.
   `teashop-backups-<random>`.  Turn on Object Lock or keep file versions
   for 30 days, so a compromised server can't erase old backups.
2. Create an application key restricted to that bucket (read and write).
3. In `/srv/teashop/.env`:
   ```
   RESTIC_REPOSITORY=b2:teashop-backups-<random>:teashop
   B2_ACCOUNT_ID=<keyID>
   B2_ACCOUNT_KEY=<applicationKey>
   ```
4. Run a backup and a restore test by hand (below), and check both pass.
5. Optional but recommended: on healthchecks.io create two checks, "backup"
   (period 1 day, grace 2 hours) and "restore test" (period 31 days, grace
   1 day), and put their ping URLs in `BACKUP_HEALTHCHECK_URL` and
   `RESTORE_HEALTHCHECK_URL`.  You get an email when either fails or
   stops running.

## Commands

On the server as `deploy`, in `/srv/teashop`:

```sh
deploy/backup-job.sh backup                                     # back up now
deploy/backup-job.sh restore-test                               # test the latest backup
docker compose --profile ops run --rm backup restic snapshots   # list backups
systemctl list-timers 'teashop-*'                               # next scheduled runs
journalctl -u teashop-backup -u teashop-restore-test --since -7d
```

The restore test downloads the latest backup, loads it into a scratch
database (`teashop_restore_test`), checks it has the shop's tables and
data, and drops it.  The live database is never touched.

`deploy/backup-job.sh` runs the job in the backup container and records
its result in the audit log, so the owner dashboard's "Operations" card
shows the last backup and restore test, and "Needs your attention" lists
a failed one, or a backup with no success for two days (a restore test:
33 days).  The timers run it too.  (Running the container directly,
`docker compose --profile ops run --rm backup [restore-test.sh]`, works
but records nothing.)  After changing the unit files in
`deploy/server/systemd/`, re-run `install-app.sh` or copy them to
`/etc/systemd/system/` and run `sudo systemctl daemon-reload`.

## Recovering

**Undo a bad deploy:** `deploy/rollback.sh --restore-db` (see
[README.md](README.md#rolling-back)).

**Restore the live database from B2** (data damaged, not caused by a deploy):

```sh
cd /srv/teashop
docker compose --profile ops run --rm backup restic snapshots      # pick a snapshot id
docker compose --profile ops run --rm backup \
    restic restore <id> --target /backups/restore --include /work/teashop.dump
docker compose stop web
docker compose exec -T db pg_restore -U teashop -d teashop --clean --if-exists --no-owner \
    < backups/restore/work/teashop.dump
docker compose up -d --wait web
```

Uploaded files: `restic restore <id> --target /backups/restore --include /data/media`,
then copy them back into the `teashop_media` volume.

**The server is gone:** create a new one and follow the first-time setup
in [README.md](README.md) up to step 4, put the old `.env` values back
(at least `RESTIC_*`, `B2_*`, `DJANGO_SECRET_KEY`, `DJANGO_ADMIN_URL`),
start the database with `docker compose up -d --wait db`, restore as
above, then run `deploy/deploy.sh`.  Practise this once before launch.
