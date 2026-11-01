#!/usr/bin/env bash
# Record a deploy, rollback, backup or restore-test result in the audit
# log, so it shows on the owner dashboard and not only in the journal.
#
#   deploy/record-ops-event.sh <kind> <succeeded|failed> [record_ops_event options]
#   deploy/record-ops-event.sh deploy succeeded --commit 0123abcd4567 --message "Deployed 0123abcd4567"
#
# kind: deploy, rollback, backup or restore_test.  Runs
# "manage.py record_ops_event" in the running build (teashop-web:current).
# Best effort: if it cannot record (no build yet, database down), it says
# so and exits 0, so recording never turns a good deploy into a failed one.
set -uo pipefail

cd "$(dirname "$0")/.."

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) record-ops-event: $*"; }

[ $# -ge 2 ] || { log "usage: $0 <kind> <succeeded|failed> [options]"; exit 2; }

# Without this check "docker compose run" would build the image itself.
if ! docker image inspect teashop-web:current >/dev/null 2>&1; then
    log "note: no teashop-web:current build to record with; $1 $2 is only in this log"
    exit 0
fi

if ! docker compose run --rm --no-deps -T web python manage.py record_ops_event "$@"; then
    log "note: could not record $1 $2 in the audit log; it is only in this log"
fi
exit 0
