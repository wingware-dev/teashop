#!/usr/bin/env bash
# Go back to an earlier build.
#
#   deploy/rollback.sh                      start the build that ran before the current one
#   deploy/rollback.sh <commit>             start that build (it must still be on the server)
#   deploy/rollback.sh --restore-db [...]   also put back the database backup taken just
#                                           before the last deploy (loses any orders or
#                                           changes made since then; asks first)
#   deploy/rollback.sh --restore-db --dump <file> [...]   restore that backup instead
#
# Deploys keep the last 5 builds and 10 pre-deploy backups (deploy.sh).
set -euo pipefail

cd "$(dirname "$0")/.."
STATE=.deploy

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) rollback: $*"; }
die() { log "ERROR: $*"; FAILURE=$*; exit 1; }

# Each rollback's result goes in the audit log (owner dashboard) as well
# as this log, once it has started (not when refused or cancelled).
STARTED=0
FAILURE=""
on_exit() {
    local status=$?
    if [ "$status" -ne 0 ] && [ "$STARTED" = 1 ]; then
        deploy/record-ops-event.sh rollback failed --commit "$TARGET" --detail "from=$CURRENT" \
            --detail "database_restored=$RESTORE_DB" \
            --message "Rollback to $TARGET failed: ${FAILURE:-a step failed (exit status $status); see the rollback log}"
    fi
}
trap on_exit EXIT

RESTORE_DB=0
DUMP=""
TARGET=""
YES=0
while [ $# -gt 0 ]; do
    case "$1" in
        --restore-db) RESTORE_DB=1 ;;
        --dump) shift; DUMP=${1:-} ;;
        --yes) YES=1 ;;
        -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
        -*) die "unknown option $1" ;;
        *) TARGET=$1 ;;
    esac
    shift
done

CURRENT=$(cat "$STATE/current" 2>/dev/null || true)
TARGET=${TARGET:-$(cat "$STATE/previous" 2>/dev/null || true)}
[ -n "$TARGET" ] || die "no earlier build recorded; give a commit"
[[ "$TARGET" =~ ^[0-9a-f]{7,40}$ ]] || die "not a commit id: $TARGET"
docker image inspect "teashop-web:$TARGET" >/dev/null 2>&1 \
    || die "the build teashop-web:$TARGET is no longer on this server; deploy it instead: deploy/deploy.sh $TARGET"

if [ "$RESTORE_DB" = 1 ]; then
    if [ -z "$DUMP" ]; then
        DUMP=$(cat "$STATE/last_predeploy_dump" 2>/dev/null || true)
        # The automatic choice is only right straight after a bad deploy:
        # the backup must be the one taken just before the running build.
        case "$DUMP" in
            *"-to-$CURRENT.dump") ;;
            *) die "the last pre-deploy backup ($DUMP) was not taken before the running build $CURRENT; pick one with --dump <file> (see backups/predeploy/)" ;;
        esac
    fi
    [ -n "$DUMP" ] && [ -s "$DUMP" ] || die "no pre-deploy backup found (looked for '${DUMP}')"
    if [ "$YES" != 1 ]; then
        echo "This replaces the live database with $DUMP."
        echo "Everything recorded since that backup (orders, stock changes) is lost."
        read -r -p "Type 'restore' to continue: " answer
        [ "$answer" = restore ] || die "cancelled"
    fi
fi

log "rolling back from ${CURRENT:-unknown} to $TARGET"
STARTED=1
# Only the app image changes.  The checkout (these scripts, compose.yaml,
# the Caddyfile) stays as it is, so a rollback never brings back older
# deploy tools; the next deploy checks out what it deploys.

if [ "$RESTORE_DB" = 1 ]; then
    log "stopping the app and restoring $DUMP"
    docker compose stop web
    docker compose up -d --wait db
    # A safety copy of the database as it is now, in case the restore was a mistake.
    mkdir -p backups/predeploy
    docker compose exec -T db pg_dump -U teashop -d teashop --format=custom \
        > "backups/predeploy/$(date -u +%Y%m%dT%H%M%SZ)-before-rollback-of-${CURRENT:-unknown}.dump"
    docker compose exec -T db pg_restore -U teashop -d teashop --clean --if-exists --no-owner --exit-on-error < "$DUMP"
fi

docker tag "teashop-web:$TARGET" teashop-web:current
docker compose up -d --wait --wait-timeout 120 web caddy || die "$TARGET did not become healthy"

[ -n "$CURRENT" ] && echo "$CURRENT" > "$STATE/previous"
echo "$TARGET" > "$STATE/current"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $TARGET rollback" >> "$STATE/history"
log "healthy; $TARGET is live"
STARTED=0
if [ "$RESTORE_DB" = 1 ]; then
    restored=" and restored the database from $DUMP"
else
    restored=""
fi
deploy/record-ops-event.sh rollback succeeded --commit "$TARGET" --detail "from=$CURRENT" \
    --detail "database_restored=$RESTORE_DB" \
    --message "Rolled back from ${CURRENT:-unknown} to $TARGET$restored"
