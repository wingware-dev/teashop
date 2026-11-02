#!/usr/bin/env bash
# Run the off-site backup or the restore test in the backup container and
# record its result in the audit log (owner dashboard).  The systemd
# timers run this; run it by hand the same way:
#
#   deploy/backup-job.sh backup
#   deploy/backup-job.sh restore-test
#
# Exits with the job's own status, so systemd still sees failures.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) backup-job: $*"; }

case "${1:-}" in
    backup) script=backup.sh kind=backup title="Backup" ;;
    restore-test) script=restore-test.sh kind=restore_test title="Restore test" ;;
    *) log "usage: $0 backup|restore-test"; exit 2 ;;
esac

output=$(mktemp)
trap 'rm -f "$output"' EXIT

docker compose --profile ops run --rm -T backup "$script" 2>&1 | tee "$output"
status=${PIPESTATUS[0]}

# The job's log lines start with a timestamp and "backup: " or
# "restore-test: "; keep the text after that.
strip() { sed -E 's/^[0-9TZ:-]+ [a-z-]+: //'; }

if [ "$status" -eq 0 ]; then
    outcome=succeeded
    # restic's "snapshot 1a2b3c4d saved" for a backup, the counts line for a restore test.
    summary=$(grep -E 'snapshot [0-9a-f]+ saved|restored: ' "$output" | tail -n 1 | strip)
    message="$title succeeded${summary:+: $summary}"
else
    outcome=failed
    # The first error is the cause; restore-test.sh ends with a bare "FAILED".
    summary=$(grep -E 'FAILED|ERROR|Fatal|fatal' "$output" | head -n 1 | strip)
    [ -n "$summary" ] || summary=$(grep -v '^[[:space:]]*$' "$output" | tail -n 1 | strip)
    message="$title failed (exit status $status)${summary:+: $summary}"
fi

deploy/record-ops-event.sh "$kind" "$outcome" --detail "exit_status=$status" --message "$message"
exit "$status"
