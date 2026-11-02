#!/usr/bin/env bash
# Set up the teashop app on a server prepared by harden.sh.  Run as root;
# safe to run again.
#
#   install-app.sh --repo git@github.com:<you>/teashop.git --domain shop.example.com \
#                  [--ci-key-file <GitHub Actions public key file>]
#
# 1. Gives the deploy account an SSH key for reading the repository (you add
#    it to GitHub as a read-only deploy key; the script stops and says so).
# 2. Clones the repository into /srv/teashop, release branch.
# 3. Writes /srv/teashop/.env with fresh random secrets (only if missing).
# 4. Lets GitHub Actions deploy with its key, limited to "deploy <commit>".
# 5. Installs the backup and restore-test timers (other daily jobs run in
#    the worker service of compose.yaml, which deploy.sh starts).
# 6. Sets up (or updates) the ops agent's limited account from this
#    checkout (ops/install-ops-account.sh) and turns its checks on in .env.
set -euo pipefail

APP_DIR=/srv/teashop
BRANCH=${BRANCH:-release}
REPO=""
DOMAIN=""
CI_KEYFILE=""

step() { echo; echo "==> $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }
as_deploy() { sudo -u deploy -H "$@"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --repo) shift; REPO=${1:-} ;;
        --domain) shift; DOMAIN=${1:-} ;;
        --ci-key-file) shift; CI_KEYFILE=${1:-} ;;
        -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
        *) die "unknown argument: $1" ;;
    esac
    shift
done

[ "$(id -u)" = 0 ] || die "run as root"
id deploy >/dev/null 2>&1 || die "no deploy account; run harden.sh first"
command -v docker >/dev/null || die "Docker is missing; run harden.sh first"
[ -n "$REPO" ] || die "--repo is required"
[[ "$DOMAIN" =~ ^[a-z0-9.-]+\.[a-z]{2,}$ ]] || die "--domain shop.example.com is required"

step "Repository access for the deploy account"
if [ ! -f /home/deploy/.ssh/id_ed25519 ]; then
    as_deploy ssh-keygen -q -t ed25519 -N "" -C "teashop-server-deploy" -f /home/deploy/.ssh/id_ed25519
fi
as_deploy sh -c 'ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null; sort -u -o ~/.ssh/known_hosts ~/.ssh/known_hosts'

if [ ! -d "$APP_DIR/.git" ]; then
    if ! as_deploy git clone --branch "$BRANCH" "$REPO" "$APP_DIR"; then
        echo
        echo "Could not clone $REPO.  Add this key on GitHub (repository Settings >"
        echo "Deploy keys > Add deploy key, read access only), then run this again:"
        echo
        cat /home/deploy/.ssh/id_ed25519.pub
        exit 1
    fi
fi

step "Settings file $APP_DIR/.env"
if [ ! -f "$APP_DIR/.env" ]; then
    secret() { python3 -c "import secrets; print(secrets.token_urlsafe(${1:-50}))"; }
    sed -e "s|^SITE_DOMAIN=.*|SITE_DOMAIN=$DOMAIN|" \
        -e "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$(secret 50)|" \
        -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(secret 32)|" \
        -e "s|^RESTIC_PASSWORD=.*|RESTIC_PASSWORD=$(secret 32)|" \
        -e "s|^DJANGO_ADMIN_URL=.*|DJANGO_ADMIN_URL=office-$(secret 6 | tr -dc 'a-zA-Z0-9' | tr 'A-Z' 'a-z')/|" \
        "$APP_DIR/.env.example" > "$APP_DIR/.env"
    chown deploy:deploy "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    echo "    Wrote $APP_DIR/.env with new secrets.  Copy RESTIC_PASSWORD to your"
    echo "    password manager now: without it the off-site backups cannot be read."
    echo "    Fill in the B2 and Sentry settings when those accounts exist."
else
    echo "    $APP_DIR/.env exists; left as is"
fi

if [ -n "$CI_KEYFILE" ]; then
    step "GitHub Actions deploy key (forced command)"
    key=$(grep -E '^(ssh-|ecdsa-)' "$CI_KEYFILE" | head -1)
    [ -n "$key" ] || die "no public key in $CI_KEYFILE"
    line="command=\"$APP_DIR/deploy/server/ssh-deploy-command.sh\",restrict $key"
    touch /home/deploy/.ssh/authorized_keys
    grep -qxF "$line" /home/deploy/.ssh/authorized_keys || echo "$line" >> /home/deploy/.ssh/authorized_keys
    chown deploy:deploy /home/deploy/.ssh/authorized_keys
    chmod 600 /home/deploy/.ssh/authorized_keys
fi

step "Backup and restore-test timers"
# The order summary and renewal reminders moved to the job worker
# (docs/jobs.md); remove their timers from servers set up before.
for retired in teashop-order-summary teashop-subscription-reminders; do
    if [ -f "/etc/systemd/system/$retired.timer" ]; then
        systemctl disable --now "$retired.timer"
        rm -f "/etc/systemd/system/$retired.timer" "/etc/systemd/system/$retired.service"
        echo "    Removed the $retired timer (the job worker runs it now)"
    fi
done
install -m 644 "$APP_DIR"/deploy/server/systemd/teashop-*.service "$APP_DIR"/deploy/server/systemd/teashop-*.timer \
    /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now teashop-backup.timer teashop-restore-test.timer
systemctl list-timers 'teashop-*' --no-pager

step "Ops agent account (docs/ops/ops-agent.md)"
# Installs the agent's commands from this checkout, so re-running this
# script after a deploy brings them up to date.
"$APP_DIR/deploy/server/ops/install-ops-account.sh"
if ! grep -q '^OPS_SERVER=.' "$APP_DIR/.env"; then
    sed -i '/^OPS_SERVER=/d' "$APP_DIR/.env"
    echo "OPS_SERVER=ssh" >> "$APP_DIR/.env"
    echo "    Turned the ops agent's server checks on (OPS_SERVER=ssh in .env); they"
    echo "    start with the next deploy."
fi

step "Done"
cat <<EOF
    First deploy (as the deploy account):
        sudo -u deploy -H $APP_DIR/deploy/deploy.sh
    Then create your owner login:
        sudo -u deploy -H docker compose -f $APP_DIR/compose.yaml exec web python manage.py createsuperuser
    and sign in at https://$DOMAIN/account/login/ to set up two-factor.
EOF
