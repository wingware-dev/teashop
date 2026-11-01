#!/usr/bin/env bash
# Back up the database and uploaded media to the restic repository
# (Backblaze B2 in production), then apply the retention policy.
#
# Runs inside the backup container:
#   docker compose --profile ops run --rm backup
# Environment: PG* (database), RESTIC_REPOSITORY, RESTIC_PASSWORD,
# B2_ACCOUNT_ID/B2_ACCOUNT_KEY for B2, BACKUP_HEALTHCHECK_URL (optional).
set -euo pipefail

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY is not set}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD is not set}"

WORK=/work
MEDIA=/data/media

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) backup: $*"; }

ping_healthcheck() {
    # $1: "" for success, "/fail" or "/start"
    if [ -n "${BACKUP_HEALTHCHECK_URL:-}" ]; then
        curl -fsS -m 10 --retry 3 -o /dev/null "${BACKUP_HEALTHCHECK_URL}$1" \
            || log "warning: could not reach the healthcheck URL"
    fi
}

on_error() {
    log "FAILED (line $1)"
    ping_healthcheck /fail
}
trap 'on_error $LINENO' ERR

ping_healthcheck /start

if ! restic cat config >/dev/null 2>&1; then
    log "initialising new repository at ${RESTIC_REPOSITORY}"
    restic init
fi

mkdir -p "$WORK"
rm -f "$WORK"/teashop.dump
log "dumping database ${PGDATABASE:-}"
pg_dump --format=custom --file "$WORK/teashop.dump"

paths=("$WORK/teashop.dump")
if [ -d "$MEDIA" ]; then
    paths+=("$MEDIA")
fi

log "uploading snapshot"
restic backup --host teashop --tag teashop "${paths[@]}"

log "applying retention: 7 daily, 5 weekly, 12 monthly"
restic forget --host teashop --tag teashop --keep-daily 7 --keep-weekly 5 --keep-monthly 12 --prune

log "checking repository structure"
restic check

rm -f "$WORK"/teashop.dump
ping_healthcheck ""
log "done"
