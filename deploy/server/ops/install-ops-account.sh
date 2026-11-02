#!/usr/bin/env bash
# Set up the ops agent's limited server account.  Run as root; harden.sh
# runs it, and install-app.sh runs it again to install newer versions of
# the agent's commands from the checkout.  Safe to run again.
#
#   install-ops-account.sh [--app-uid 10001]
#
# What it sets up (docs/ops/ops-agent.md explains each):
#   - the "teashop-ops" account: no password, no sudo group, no Docker
#   - /usr/local/sbin/teashop-ops-command (what its SSH key may run) and
#     /usr/local/sbin/teashop-ops-helper (the root part), owned by root
#   - /etc/sudoers.d/91-teashop-ops: the helper, with the exact arguments
#     in ops-helper.sh, and nothing else
#   - an SSH key for the app's job worker in /etc/teashop/ops-agent,
#     readable only by the container's user (uid 10001), and the server's
#     host key there so the worker can check whom it talks to
#   - ~teashop-ops/.ssh/authorized_keys, owned by root: that key, limited
#     to teashop-ops-command and to addresses on this server's private
#     networks (the containers)
#   - adds teashop-ops to the SSH AllowUsers list if harden.sh wrote one
set -euo pipefail

OPS_USER=teashop-ops
APP_UID=10001
KEY_DIR=${TEASHOP_OPS_KEY_DIR:-/etc/teashop/ops-agent}
SBIN=/usr/local/sbin
SSHD_CONF=/etc/ssh/sshd_config.d/10-teashop-hardening.conf
HERE=$(cd "$(dirname "$0")" && pwd)
# The containers reach the server from Docker's private networks.
FROM="10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,127.0.0.1,::1"

note() { echo "    $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
    case "$1" in
        --app-uid) shift; APP_UID=${1:-} ;;
        -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
        *) die "unknown argument: $1" ;;
    esac
    shift
done

[ "$(id -u)" = 0 ] || die "run as root"
[[ "$APP_UID" =~ ^[0-9]+$ ]] || die "--app-uid must be a number"
for file in ops-command.py ops-helper.sh; do
    [ -s "$HERE/$file" ] || die "$HERE/$file is missing"
done

if ! id "$OPS_USER" >/dev/null 2>&1; then
    # A login shell is needed for SSH to start the forced command.
    adduser --disabled-password --gecos "teashop ops agent" --shell /bin/sh "$OPS_USER"
fi
# Never in the sudo or docker groups, whatever happened before.
for group in sudo docker adm; do
    if id -nG "$OPS_USER" | tr ' ' '\n' | grep -qx "$group"; then
        gpasswd -d "$OPS_USER" "$group" >/dev/null
        note "removed $OPS_USER from group $group"
    fi
done

install -m 755 -o root -g root "$HERE/ops-command.py" "$SBIN/teashop-ops-command"
install -m 755 -o root -g root "$HERE/ops-helper.sh" "$SBIN/teashop-ops-helper"

helper="$SBIN/teashop-ops-helper"
sudoers=$(mktemp)
cat > "$sudoers" <<EOF
# Written by teashop deploy/server/ops/install-ops-account.sh.  The ops
# agent's account may run the helper with exactly these arguments.
Cmnd_Alias TEASHOP_OPS = $helper containers, \\
    $helper fail2ban, \\
    $helper journal-usage, \\
    $helper logs ssh, $helper logs upgrades, $helper logs web, \\
    $helper logs worker, $helper logs caddy, $helper logs db, \\
    $helper apply-security-updates, \\
    $helper rotate-logs
Defaults:$OPS_USER !requiretty, env_reset
$OPS_USER ALL=(root) NOPASSWD: TEASHOP_OPS
EOF
visudo -cqf "$sudoers" || { rm -f "$sudoers"; die "visudo rejected the ops agent's sudoers file"; }
install -m 440 -o root -g root "$sudoers" /etc/sudoers.d/91-teashop-ops
rm -f "$sudoers"

# The job worker's key.  The container runs as uid $APP_UID, which needs
# to read it; nobody else on the server does.
install -d -m 755 -o root -g root "$(dirname "$KEY_DIR")"
install -d -m 700 -o "$APP_UID" -g "$APP_UID" "$KEY_DIR"
if [ ! -s "$KEY_DIR/id_ed25519" ]; then
    ssh-keygen -q -t ed25519 -N "" -C "teashop-ops-agent" -f "$KEY_DIR/id_ed25519"
    note "made the ops agent's SSH key in $KEY_DIR"
fi
chown "$APP_UID:$APP_UID" "$KEY_DIR/id_ed25519" "$KEY_DIR/id_ed25519.pub"
chmod 600 "$KEY_DIR/id_ed25519"
[ -f /etc/ssh/ssh_host_ed25519_key.pub ] || ssh-keygen -A
echo "host.docker.internal $(cut -d' ' -f1,2 /etc/ssh/ssh_host_ed25519_key.pub)" > "$KEY_DIR/known_hosts"
chown "$APP_UID:$APP_UID" "$KEY_DIR/known_hosts"
chmod 644 "$KEY_DIR/known_hosts"

# authorized_keys belongs to root, so the account cannot widen its own key.
home=$(getent passwd "$OPS_USER" | cut -d: -f6)
install -d -m 755 -o root -g root "$home/.ssh"
echo "command=\"$SBIN/teashop-ops-command\",restrict,from=\"$FROM\" $(cat "$KEY_DIR/id_ed25519.pub")" \
    > "$home/.ssh/authorized_keys"
chown root:root "$home/.ssh/authorized_keys"
chmod 644 "$home/.ssh/authorized_keys"

if [ -f "$SSHD_CONF" ] && grep -q '^AllowUsers ' "$SSHD_CONF" && ! grep -q "^AllowUsers .*\b$OPS_USER\b" "$SSHD_CONF"; then
    sed -i "s/^AllowUsers .*/& $OPS_USER/" "$SSHD_CONF"
    sshd -t || die "sshd rejected the new AllowUsers line in $SSHD_CONF"
    if [ -d /run/systemd/system ]; then systemctl reload ssh; fi
    note "added $OPS_USER to AllowUsers"
fi
note "ops agent account ready: $OPS_USER, key in $KEY_DIR"
