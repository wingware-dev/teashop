#!/usr/bin/env bash
# Deploy a commit: build its image, check its settings, back up the
# database, migrate, start it and wait until it is healthy.  If the new
# version does not come up healthy, the previous one is started again.
#
# Usage, from the checkout on the server (/srv/teashop):
#   deploy/deploy.sh            deploy what is checked out
#   deploy/deploy.sh <commit>   fetch, check out <commit>, deploy it
#
# GitHub Actions runs this over SSH on each push to the release branch.
# See docs/ops/README.md.
set -euo pipefail

cd "$(dirname "$0")/.."
STATE=.deploy
PREDEPLOY_DIR=backups/predeploy
KEEP_DUMPS=${KEEP_DUMPS:-10}
KEEP_IMAGES=${KEEP_IMAGES:-5}

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) deploy: $*"; }
die() { log "ERROR: $*"; FAILURE=$*; exit 1; }

# Each deploy's result goes in the audit log (owner dashboard) as well as
# this log.  A failure is recorded on the way out, whatever stopped us.
SHA=""
PREVIOUS=""
FAILURE=""
RECORDED=0
record() { deploy/record-ops-event.sh deploy "$@"; RECORDED=1; }
on_exit() {
    local status=$?
    if [ "$status" -ne 0 ] && [ -n "$SHA" ] && [ "$RECORDED" = 0 ]; then
        record failed --commit "$SHA" --detail "previous=$PREVIOUS" \
            --message "Deploy failed: ${FAILURE:-a step failed for $SHA (exit status $status); see the deploy log}"
    fi
}
trap on_exit EXIT

# The job worker (docs/jobs.md) runs the same build as web.  Builds from
# before the job queue have none (they send emails themselves), so it is
# stopped when going back to one.
start_worker() {
    if docker run --rm --no-healthcheck --entrypoint test "teashop-web:$1" -f apps/jobs/worker.py; then
        docker compose up -d --wait --wait-timeout 120 worker
    else
        log "teashop-web:$1 has no job worker; stopping the worker"
        docker compose stop worker
    fi
}

[ -f .env ] || die ".env is missing (copy .env.example)"

if [ $# -gt 1 ]; then
    die "usage: $0 [commit]"
elif [ $# -eq 1 ]; then
    [[ "$1" =~ ^[0-9a-f]{7,40}$ ]] || die "not a commit id: $1"
    log "fetching and checking out $1"
    git fetch --quiet origin
    git checkout --quiet --detach "$1"
fi

if [ -n "$(git status --porcelain --untracked-files=no)" ] && [ "${ALLOW_DIRTY:-}" != 1 ]; then
    die "the checkout has uncommitted changes; commit them or set ALLOW_DIRTY=1"
fi

SHA=$(git rev-parse --short=12 HEAD)
mkdir -p "$STATE" "$PREDEPLOY_DIR"
PREVIOUS=$(cat "$STATE/current" 2>/dev/null || true)
log "deploying $SHA (running now: ${PREVIOUS:-nothing})"

log "building image teashop-web:$SHA"
docker build --quiet --build-arg GIT_SHA="$SHA" -t "teashop-web:$SHA" . >/dev/null

# Run a one-off command in the new build, with the server's real settings.
in_new_build() { TEASHOP_TAG="$SHA" docker compose run --rm --no-deps -T web "$@"; }

log "checking the new build's production settings"
in_new_build python manage.py check --deploy --fail-level WARNING \
    || die "settings check failed for $SHA; nothing was changed"

docker compose up -d --wait db

DUMP="$PREDEPLOY_DIR/$(date -u +%Y%m%dT%H%M%SZ)-${PREVIOUS:-none}-to-$SHA.dump"
log "backing up the database to $DUMP"
docker compose exec -T db pg_dump -U teashop -d teashop --format=custom > "$DUMP.partial"
mv "$DUMP.partial" "$DUMP"
echo "$DUMP" > "$STATE/last_predeploy_dump"
ls -1t "$PREDEPLOY_DIR"/*.dump | tail -n +$((KEEP_DUMPS + 1)) | while read -r old; do rm -f "$old"; done

log "applying database migrations"
in_new_build python manage.py migrate --noinput \
    || die "migrations of $SHA failed; $PREVIOUS still runs.  If the database was left half-migrated: deploy/rollback.sh --restore-db"

log "starting $SHA"
docker tag "teashop-web:$SHA" teashop-web:current
if docker compose up -d --wait --wait-timeout 120 web worker caddy; then
    if [ -n "$PREVIOUS" ] && [ "$PREVIOUS" != "$SHA" ]; then
        echo "$PREVIOUS" > "$STATE/previous"
    fi
    echo "$SHA" > "$STATE/current"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $SHA" >> "$STATE/history"
    log "healthy; $SHA is live"
    record succeeded --commit "$SHA" --detail "previous=$PREVIOUS" \
        --message "Deployed $SHA (replacing ${PREVIOUS:-nothing})"
else
    log "$SHA did not become healthy; recent web log:"
    docker compose logs --tail 40 web || true
    if [ -n "$PREVIOUS" ]; then
        log "starting $PREVIOUS again"
        docker tag "teashop-web:$PREVIOUS" teashop-web:current
        docker compose up -d --wait --wait-timeout 120 web caddy \
            || log "the previous version is not healthy either"
        start_worker "$PREVIOUS" || log "the previous version's job worker is not healthy"
    fi
    die "deploy of $SHA failed.  If its migrations broke the old version: deploy/rollback.sh --restore-db"
fi

# Keep the builds of the last few deploys, for rollback; remove older ones.
keep=$(awk '{sha[NR] = $2} END {for (i = NR; i > 0; i--) if (!seen[sha[i]]++) print sha[i]}' "$STATE/history" \
    | head -n "$KEEP_IMAGES")
docker image ls teashop-web --format '{{.Tag}}' | while read -r tag; do
    case "$tag" in current|local|"$SHA"|"$PREVIOUS") continue ;; esac
    if ! grep -qx "$tag" <<< "$keep"; then
        docker image rm "teashop-web:$tag" >/dev/null 2>&1 || log "note: could not remove old image $tag"
    fi
done
