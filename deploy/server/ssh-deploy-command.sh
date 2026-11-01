#!/usr/bin/env bash
# Forced command for the CI deploy key.  In ~deploy/.ssh/authorized_keys:
#
#   command="/srv/teashop/deploy/server/ssh-deploy-command.sh",restrict ssh-ed25519 AAAA... github-actions
#
# Whatever the client asks to run, SSH runs this instead, and this only
# accepts "deploy <commit id>".  A leaked CI key can therefore deploy a
# commit that is already in the repository, and nothing else.
set -euo pipefail

APP_DIR=${TEASHOP_APP_DIR:-/srv/teashop}
DEPLOY=${TEASHOP_DEPLOY_SCRIPT:-$APP_DIR/deploy/deploy.sh}

request=${SSH_ORIGINAL_COMMAND:-}
if [[ "$request" =~ ^deploy\ ([0-9a-f]{40})$ ]]; then
    sha=${BASH_REMATCH[1]}
    logger -t teashop-deploy "CI deploy of $sha requested" 2>/dev/null || true
    if command -v flock >/dev/null; then
        # One deploy at a time; a second one fails instead of queueing.
        mkdir -p "$APP_DIR/.deploy"
        exec flock --nonblock "$APP_DIR/.deploy/lock" "$DEPLOY" "$sha"
    fi
    exec "$DEPLOY" "$sha"
fi

echo "refused: only 'deploy <40-character commit id>' is allowed" >&2
logger -t teashop-deploy "refused CI command: ${request:0:200}" 2>/dev/null || true
exit 2
