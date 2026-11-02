"""Deployment checks (manage.py check --deploy) for checkout settings."""

from django.conf import settings
from django.core.checks import Warning, register


@register(deploy=True)
def checkout_settings(app_configs, **kwargs):
    problems = []
    if not settings.EMAIL_HOST:
        problems.append(Warning("EMAIL_HOST is not set: order emails are printed, not sent.", id="checkout.W001"))
    if settings.PAYMENT_PROVIDER != "stripe":
        problems.append(Warning("Stripe is not set up: checkout stays closed.", id="checkout.W002"))
    elif not settings.STRIPE_WEBHOOK_SECRET:
        problems.append(Warning("STRIPE_WEBHOOK_SECRET is not set: orders cannot be marked paid.",
                                id="checkout.W003"))
    if settings.SHIPPING_PROVIDER != "easypost" or not settings.SHIP_FROM["zip"]:
        problems.append(Warning("EasyPost or the SHIP_FROM_* address is not set: checkout stays closed.",
                                id="checkout.W004"))
    if not settings.SHOP_POSTAL_ADDRESS:
        problems.append(Warning("SHOP_POSTAL_ADDRESS is not set: emails and policies need a postal address "
                                "(CAN-SPAM).", id="checkout.W005"))
    if settings.SITE_URL.startswith("http://localhost"):
        problems.append(Warning("SITE_URL is not set: links in emails point at localhost.", id="checkout.W006"))
    return problems
