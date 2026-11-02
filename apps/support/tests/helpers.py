"""Shared settings and builders for the support tests."""

import time
from email.message import EmailMessage

from apps.checkout import protection
from apps.fulfillment.testing import paid_order, size
from apps.storefront import demo

SUPPORT_SETTINGS = dict(
    STOREFRONT_OPEN=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    TURNSTILE_SITE_KEY="", TURNSTILE_SECRET_KEY="", CHECKOUT_MIN_FORM_SECONDS=0,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "support-tests"}},
    OWNER_NOTIFY_EMAIL="owner@example.com", SUPPORT_EMAIL="help@teashop.example", SITE_URL="https://shop.example",
    AGENTS_LIVE=[], SUPPORT_INBOX="", SUPPORT_READY_MIN_DRAFTS=3, SUPPORT_READY_RATE=0.9,
    PAYMENT_PROVIDER="fake", SHIPPING_PROVIDER="fake", JOBS_EAGER=True,
)


def catalog():
    demo.load()


def order(email="ada@example.com"):
    return paid_order([(size("assam-second-flush"), 1)], email=email)


def form_data(**extra):
    return {protection.STAMP_FIELD: protection.form_stamp(time.time() - 60), **extra}


def raw_email(body="Where is my order?", *, sender="Ada <ada@example.com>", subject="My order", headers=None,
              html=None):
    message = EmailMessage()
    message["From"] = sender
    message["To"] = "help@teashop.example"
    message["Subject"] = subject
    message["Message-ID"] = f"<{abs(hash((body, subject, sender, str(headers))))}@mail.example>"
    for name, value in (headers or {}).items():
        message[name] = value
    if html is not None:
        message.set_content(html, subtype="html")
    else:
        message.set_content(body)
    return message.as_bytes()
