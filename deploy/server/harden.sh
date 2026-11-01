#!/usr/bin/env bash
# Harden a fresh Ubuntu 24.04 LTS server for the teashop.  Run as root on
# the new server; safe to run again (each step checks what is there).
#
#   harden.sh --admin <name> [--admin-key-file <public key file>] [--skip-docker]
#
# What it does (docs/ops/README.md explains each):
#   - installs all updates, then turns on automatic security updates with
#     automatic reboots at 04:30 server time (UTC) when one is needed
#   - creates your admin account (sudo, SSH key only) and a "deploy" account
#   - SSH: keys only, no root login, no passwords, only those two accounts
#   - firewall (ufw): only SSH (rate-limited), HTTP and HTTPS in
#   - fail2ban: bans addresses that keep failing SSH logins
#   - Docker from Docker's own repository, with log rotation for containers
#   - caps the system journal at 500 MB, adds swap on small servers
#
# The admin account gets the SSH keys from --admin-key-file, or else the
# keys root has now (most VPS providers put yours there).  The script stops
# before changing SSH if the admin account would end up with no key, so it
# cannot lock you out.  Keep your current SSH session open until you have
# logged in as the admin account in a second terminal.
set -euo pipefail

ADMIN=""
KEYFILE=""
SKIP_DOCKER=0
REBOOT_TIME=${REBOOT_TIME:-04:30}
APP_DIR=/srv/teashop

step() { echo; echo "==> $*"; }
note() { echo "    $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
    case "$1" in
        --admin) shift; ADMIN=${1:-} ;;
        --admin-key-file) shift; KEYFILE=${1:-} ;;
        --skip-docker) SKIP_DOCKER=1 ;;
        -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
        *) die "unknown argument: $1" ;;
    esac
    shift
done

[ "$(id -u)" = 0 ] || die "run as root (sudo $0 ...)"
[[ "$ADMIN" =~ ^[a-z][a-z0-9_-]{1,30}$ ]] || die "--admin <name> is required (lowercase letters, digits, - and _)"
[ "$ADMIN" != deploy ] && [ "$ADMIN" != root ] || die "--admin must not be 'deploy' or 'root'"
[ -z "$KEYFILE" ] || [ -s "$KEYFILE" ] || die "key file $KEYFILE is missing or empty"

. /etc/os-release
[ "$ID" = ubuntu ] || die "this script is for Ubuntu (found $ID)"
[ "$VERSION_ID" = 24.04 ] || note "warning: written for Ubuntu 24.04, this is $VERSION_ID"

# Without systemd (a test container) services are configured, not started.
if [ -d /run/systemd/system ]; then SYSTEMD=1; else SYSTEMD=0; note "no systemd: configuring only"; fi
svc() { if [ "$SYSTEMD" = 1 ]; then systemctl "$@"; else note "(skipped: systemctl $*)"; fi; }

export DEBIAN_FRONTEND=noninteractive
APT_OPTS=(-y -q -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold)

step "Installing updates and security tools"
apt-get update -q
apt-get "${APT_OPTS[@]}" upgrade
apt-get "${APT_OPTS[@]}" install unattended-upgrades apt-listchanges ufw fail2ban \
    openssh-server ca-certificates curl git gnupg sudo logrotate

step "Admin account: $ADMIN"
if ! id "$ADMIN" >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" "$ADMIN"
fi
usermod -aG sudo "$ADMIN"
# The admin has no password (SSH keys only), so sudo cannot ask for one.
echo "$ADMIN ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/90-teashop-$ADMIN"
chmod 440 "/etc/sudoers.d/90-teashop-$ADMIN"
visudo -cq

add_keys() {  # add_keys <user> <file>: append keys the user doesn't have yet
    local user=$1 src=$2 home
    home=$(getent passwd "$user" | cut -d: -f6)
    install -d -m 700 -o "$user" -g "$user" "$home/.ssh"
    touch "$home/.ssh/authorized_keys"
    while IFS= read -r key; do
        [[ "$key" =~ ^(ssh-|ecdsa-|sk-) ]] || continue
        grep -qxF "$key" "$home/.ssh/authorized_keys" || echo "$key" >> "$home/.ssh/authorized_keys"
    done < "$src"
    chown "$user:$user" "$home/.ssh/authorized_keys"
    chmod 600 "$home/.ssh/authorized_keys"
}
if [ -n "$KEYFILE" ]; then
    add_keys "$ADMIN" "$KEYFILE"
elif [ -s /root/.ssh/authorized_keys ]; then
    add_keys "$ADMIN" /root/.ssh/authorized_keys
fi
ADMIN_HOME=$(getent passwd "$ADMIN" | cut -d: -f6)
grep -qE '^(ssh-|ecdsa-|sk-)' "$ADMIN_HOME/.ssh/authorized_keys" 2>/dev/null \
    || die "$ADMIN has no SSH key; give --admin-key-file.  SSH settings were not changed."

step "Deploy account (runs the app; used by GitHub Actions)"
if ! id deploy >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" deploy
fi
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
install -d -m 755 -o deploy -g deploy "$APP_DIR"

step "SSH: keys only, no root login"
cat > /etc/ssh/sshd_config.d/10-teashop-hardening.conf <<EOF
# Written by teashop deploy/server/harden.sh.  The first value sshd reads
# wins, so this file comes before the provider's (50-cloud-init.conf).
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
PermitEmptyPasswords no
MaxAuthTries 3
LoginGraceTime 30
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers $ADMIN deploy
EOF
mkdir -p /run/sshd
[ -f /etc/ssh/ssh_host_ed25519_key ] || ssh-keygen -A
sshd -t || die "sshd rejected the new settings; fix /etc/ssh/sshd_config.d/10-teashop-hardening.conf"
svc reload ssh

step "Firewall: SSH (rate-limited), HTTP, HTTPS"
ufw default deny incoming
ufw default allow outgoing
ufw limit 22/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP (redirects to HTTPS, certificate renewal)"
ufw allow 443/tcp comment "HTTPS"
ufw allow 443/udp comment "HTTP/3"
if [ "$SYSTEMD" = 1 ]; then ufw --force enable; else note "(skipped: ufw enable)"; fi

step "Automatic security updates, reboot at $REBOOT_TIME when needed"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
cat > /etc/apt/apt.conf.d/52teashop-unattended-upgrades <<EOF
// Written by teashop deploy/server/harden.sh; adds to 50unattended-upgrades.
Unattended-Upgrade::Origins-Pattern {
    // Docker's packages, which come from Docker's own repository.
    "origin=Docker";
};
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-WithUsers "true";
Unattended-Upgrade::Automatic-Reboot-Time "$REBOOT_TIME";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
EOF
svc enable --now unattended-upgrades

step "fail2ban: ban repeated SSH login failures"
cat > /etc/fail2ban/jail.d/teashop.local <<EOF
# Written by teashop deploy/server/harden.sh
[DEFAULT]
backend = systemd
findtime = 10m
maxretry = 5
bantime = 1h
bantime.increment = true
bantime.maxtime = 1w

[sshd]
enabled = true
mode = aggressive
EOF
svc enable fail2ban
svc restart fail2ban

step "System journal capped at 500 MB, server clock in UTC"
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/teashop.conf <<EOF
[Journal]
SystemMaxUse=500M
MaxRetentionSec=3month
EOF
svc restart systemd-journald
if [ "$SYSTEMD" = 1 ]; then timedatectl set-timezone UTC; else ln -sf /usr/share/zoneinfo/UTC /etc/localtime; fi

if [ "$SKIP_DOCKER" = 0 ]; then
    step "Docker (from Docker's repository) with container log rotation"
    install -m 0755 -d /etc/apt/keyrings
    if [ ! -s /etc/apt/keyrings/docker.asc ]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
    fi
    cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $VERSION_CODENAME
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF
    apt-get update -q
    apt-get "${APT_OPTS[@]}" install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {"max-size": "10m", "max-file": "5"},
  "live-restore": true,
  "no-new-privileges": true
}
EOF
    svc enable docker
    svc restart docker
    # Docker access is root-equivalent: only the deploy account gets it.
    usermod -aG docker deploy
else
    note "skipping Docker (--skip-docker)"
fi

if [ "$SYSTEMD" = 1 ] && ! swapon --show | grep -q . ; then
    mem_mb=$(awk '/MemTotal/ {print int($2 / 1024)}' /proc/meminfo)
    if [ "$mem_mb" -lt 8192 ]; then
        step "Adding a 2 GB swap file (server has ${mem_mb} MB of memory)"
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
fi

step "Done"
cat <<EOF
    Next, in a NEW terminal (keep this one open until it works):
        ssh $ADMIN@<server address>
        sudo true
    Then install the app with install-app.sh (see docs/ops/README.md).
EOF
