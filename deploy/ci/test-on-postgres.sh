#!/usr/bin/env bash
# Run the tests on PostgreSQL, as CI does (.github/workflows/ci.yml), in a
# throwaway postgres:17-alpine container.  Development and Wing's Testing
# tool use SQLite, which misses PostgreSQL-only failures (row locks across
# outer joins, the audit log's append-only trigger, closed connections).
# Needs Docker.
#
#   deploy/ci/test-on-postgres.sh                 the whole suite (test apps)
#   deploy/ci/test-on-postgres.sh apps.marketing  any manage.py test arguments
#   deploy/ci/test-on-postgres.sh start           leave the database running,
#                                                 for Wing's Testing tool
#   deploy/ci/test-on-postgres.sh stop            remove it
#
# With the database started, run tests in Wing against it by setting
# DATABASE_URL to the URL "start" prints (Project Properties > Environment,
# or a launch configuration).  TEST_PG_PORT picks the port (default 55432).
set -euo pipefail

cd "$(dirname "$0")/../.."

NAME=teashop-test-postgres
IMAGE=postgres:17-alpine
PORT=${TEST_PG_PORT:-55432}
URL="postgres://teashop:teashop@localhost:$PORT/teashop"
PYTHON=${PYTHON:-.venv/bin/python}

log() { echo "test-on-postgres: $*" >&2; }

running() { [ -n "$(docker ps -q --filter "name=^${NAME}$")" ]; }

start() {
    if running; then
        return
    fi
    log "starting $IMAGE on port $PORT"
    # tmpfs: the data is thrown away with the container, and tests run faster.
    docker run -d --rm --name "$NAME" --tmpfs /var/lib/postgresql/data \
        -e POSTGRES_DB=teashop -e POSTGRES_USER=teashop -e POSTGRES_PASSWORD=teashop \
        -p "127.0.0.1:$PORT:5432" "$IMAGE" >/dev/null
    for _ in $(seq 60); do
        # pg_isready over TCP: the image's first-run setup listens only on
        # the socket, so this waits for the real server.
        if docker exec "$NAME" pg_isready -q -h 127.0.0.1 -U teashop -d teashop; then
            return
        fi
        sleep 1
    done
    log "PostgreSQL did not start; its log:"
    docker logs "$NAME" >&2 || true
    stop
    exit 1
}

stop() {
    if running; then
        docker stop "$NAME" >/dev/null
    fi
}

case "${1:-}" in
    start)
        start
        echo "DATABASE_URL=$URL"
        ;;
    stop)
        stop
        ;;
    *)
        # Leave a database the user started with "start" running.
        if running; then
            started=no
        else
            started=yes
            start
        fi
        if [ "$started" = yes ]; then
            trap stop EXIT
        fi
        [ $# -gt 0 ] || set -- apps
        DATABASE_URL=$URL "$PYTHON" manage.py test "$@"
        ;;
esac
