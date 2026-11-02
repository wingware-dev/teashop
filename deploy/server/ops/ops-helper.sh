#!/usr/bin/env bash
# The ops agent's only way to act as root.  Installed as
# /usr/local/sbin/teashop-ops-helper (owned by root) by install-ops-account.sh.
# /etc/sudoers.d/91-teashop-ops lets the teashop-ops account run it with
# exactly these arguments, and nothing else:
#
#   containers                 the app's containers and their health
#   fail2ban                   SSH ban counts
#   journal-usage              size of the system journal
#   logs ssh|upgrades|web|worker|caddy|db
#                              the last day of one log (read only)
#   apply-security-updates     refresh the package lists, then run
#                              unattended-upgrade (security updates only)
#   rotate-logs                logrotate, then trim the journal to 400 MB
#
# Each command is fixed here; nothing the caller passes reaches a shell or
# another program's options.
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LC_ALL=C.UTF-8

refuse() { echo "refused: $*" >&2; exit 2; }

[ $# -ge 1 ] && [ $# -le 2 ] || refuse "one command, with one log name for logs"
verb=$1
arg=${2:-}
[ -z "$arg" ] || [ "$verb" = logs ] || refuse "$verb takes no arguments"

case "$verb" in
    containers)
        docker ps --all --filter label=com.docker.compose.project=teashop \
            --format '{{.Names}}{{"\t"}}{{.Status}}'
        ;;
    fail2ban)
        fail2ban-client status sshd
        ;;
    journal-usage)
        journalctl --disk-usage
        ;;
    logs)
        case "$arg" in
            ssh) journalctl -u ssh --since -24h --no-pager -o short-iso ;;
            upgrades) tail -n 300 /var/log/unattended-upgrades/unattended-upgrades.log 2>/dev/null || true ;;
            web|worker|caddy|db) docker logs --since 24h --tail 5000 "teashop-$arg-1" 2>&1 ;;
            *) refuse "no log named '$arg'" ;;
        esac
        ;;
    apply-security-updates)
        export DEBIAN_FRONTEND=noninteractive
        apt-get -q update
        unattended-upgrade -v
        ;;
    rotate-logs)
        logrotate /etc/logrotate.conf
        journalctl --vacuum-size=400M --vacuum-time=3month
        ;;
    *)
        refuse "unknown command '$verb'"
        ;;
esac
