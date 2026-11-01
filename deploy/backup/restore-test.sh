#!/usr/bin/env bash
# Prove the latest backup can be restored: download it, load the database
# dump into a scratch database on the same server, check it holds the
# shop's tables and data, then drop the scratch database.  The live
# database is never touched.
#
#   docker compose --profile ops run --rm backup restore-test.sh
set -euo pipefail

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY is not set}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD is not set}"

SCRATCH_DB=teashop_restore_test
TARGET=$(mktemp -d)

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) restore-test: $*"; }

ping_healthcheck() {
    # $1: "" for success or "/fail"
    if [ -n "${RESTORE_HEALTHCHECK_URL:-}" ]; then
        curl -fsS -m 10 --retry 3 -o /dev/null "${RESTORE_HEALTHCHECK_URL}$1" \
            || log "warning: could not reach the healthcheck URL"
    fi
}

cleanup() {
    status=$?
    dropdb --if-exists "$SCRATCH_DB" >/dev/null 2>&1 || log "warning: could not drop $SCRATCH_DB"
    rm -rf "$TARGET"
    if [ "$status" -ne 0 ]; then
        log "FAILED"
        ping_healthcheck /fail
    fi
}
trap cleanup EXIT

log "restoring latest snapshot from ${RESTIC_REPOSITORY}"
restic restore latest --host teashop --tag teashop --target "$TARGET" --include /work/teashop.dump
DUMP="$TARGET/work/teashop.dump"
[ -s "$DUMP" ] || { log "FAILED: snapshot has no database dump"; exit 1; }

snapshot_time=$(restic snapshots latest --host teashop --tag teashop --json | sed -n 's/.*"time":"\([^"]*\)".*/\1/p' | head -1)
log "snapshot taken at ${snapshot_time:-unknown}"

dropdb --if-exists "$SCRATCH_DB"
createdb "$SCRATCH_DB"
pg_restore --no-owner --exit-on-error --dbname "$SCRATCH_DB" "$DUMP"

q() { psql --dbname "$SCRATCH_DB" --tuples-only --no-align --command "$1"; }
migrations=$(q "SELECT count(*) FROM django_migrations")
users=$(q "SELECT count(*) FROM auth_user")
events=$(q "SELECT count(*) FROM audit_auditevent")
log "restored: $migrations migrations applied, $users users, $events audit events"

if [ "$migrations" -lt 1 ]; then
    log "FAILED: restored database has no applied migrations"
    exit 1
fi
log "PASSED"
ping_healthcheck ""
