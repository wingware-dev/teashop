"""Keeping bots and card testers off the checkout and sign-in forms.

Layers, cheapest first:

- a honeypot field people never see (hidden by CSS) that bots fill in;
- a signed time stamp: a form sent back faster than a person could fill
  it is refused;
- a limit on submissions per visitor address per hour;
- Cloudflare Turnstile, when its keys are set (settings.TURNSTILE_*).

Stripe Radar screens the payments themselves.  check() returns a message
for the visitor when a submission is refused, and logs why.
"""

import logging
import time

import requests
from django.conf import settings
from django.core import signing
from django.core.cache import cache

from apps.core.net import client_ip

log = logging.getLogger(__name__)

HONEYPOT_FIELD = "website"
STAMP_FIELD = "form_stamp"
STAMP_SALT = "checkout.form-stamp"
TURNSTILE_FIELD = "cf-turnstile-response"
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
REFUSED = "Sorry, we could not accept that.  Please wait a moment and try again."


def form_stamp(at=None):
    return signing.dumps(at if at is not None else time.time(), salt=STAMP_SALT)


def turnstile_enabled():
    return bool(settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY)


def context():
    """What forms protected by check() need in their template."""
    return {"form_stamp": form_stamp(), "turnstile_site_key": settings.TURNSTILE_SITE_KEY if turnstile_enabled()
            else "", "honeypot_field": HONEYPOT_FIELD}


def over_limit(request, scope, limit):
    """Count one submission to scope from this address; True past limit an hour."""
    key = f"checkout-limit:{scope}:{client_ip(request)}"
    cache.add(key, 0, timeout=3600)
    try:
        count = cache.incr(key)
    except ValueError:  # expired between add and incr
        cache.set(key, 1, timeout=3600)
        count = 1
    return count > limit


def check(request, scope, limit=None):
    """None if the POSTed form looks like a person sent it, else a message."""
    data = request.POST
    if data.get(HONEYPOT_FIELD):
        log.warning("Refused %s: honeypot filled from %s", scope, client_ip(request))
        return REFUSED
    try:
        stamped = signing.loads(data.get(STAMP_FIELD, ""), salt=STAMP_SALT, max_age=24 * 3600)
    except signing.BadSignature:
        log.warning("Refused %s: missing or bad form stamp from %s", scope, client_ip(request))
        return "This page was open too long.  Please try again."
    if time.time() - float(stamped) < settings.CHECKOUT_MIN_FORM_SECONDS:
        log.warning("Refused %s: sent too fast from %s", scope, client_ip(request))
        return REFUSED
    if over_limit(request, scope, limit or settings.CHECKOUT_RATE_LIMIT):
        log.warning("Refused %s: rate limit reached by %s", scope, client_ip(request))
        return "Too many tries from your connection.  Please wait an hour, or write to us."
    if turnstile_enabled() and not turnstile_passed(request):
        return "Please complete the check that you are not a bot."
    return None


def turnstile_passed(request):
    token = request.POST.get(TURNSTILE_FIELD, "")
    if not token:
        return False
    try:
        response = requests.post(TURNSTILE_VERIFY_URL, timeout=10, data={
            "secret": settings.TURNSTILE_SECRET_KEY, "response": token, "remoteip": client_ip(request)})
        return bool(response.json().get("success"))
    except (requests.RequestException, ValueError):
        # Cloudflare unreachable: let the person through rather than lose
        # the order; the other layers still apply.
        log.exception("Turnstile check failed; allowing the submission")
        return True
