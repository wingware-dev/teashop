"""Shared set-up for checkout tests: the demo catalog, and a session-backed
walk through the checkout with the stand-in providers."""

import time
from decimal import Decimal
from types import SimpleNamespace

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.catalog.models import Product, SizeOption
from apps.checkout import protection
from apps.storefront import demo

# The stand-ins, an open shop, no form-speed check, and the cache-based
# limits reset per test by using a unique scope cache.
CHECKOUT_TEST_SETTINGS = dict(
    STOREFRONT_OPEN=True, PAYMENT_PROVIDER="fake", SHIPPING_PROVIDER="fake", TAX_PROVIDER="table",
    TURNSTILE_SITE_KEY="", TURNSTILE_SECRET_KEY="", CHECKOUT_MIN_FORM_SECONDS=0, OWNER_NOTIFY_EMAIL="owner@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "checkout-tests"}},
)
checkout_settings = override_settings(**CHECKOUT_TEST_SETTINGS)


@checkout_settings
class CheckoutTestCase(TestCase):
    """Checkout settings for tests, and a fresh cache (rate limits) each test."""

    def setUp(self):
        super().setUp()
        cache.clear()

ADDRESS = {"email": "Ada@Example.com", "name": "Ada Lovelace", "street1": "12 Main St", "street2": "",
           "city": "Albany", "state": "NY", "zip": "12207", "phone": ""}


def load_catalog():
    demo.load()
    return tea_size(), goods_size()


def tea_size():
    return SizeOption.objects.filter(product__slug="assam-second-flush").order_by("price").first()


def goods_size():
    return SizeOption.objects.get(product__slug="glass-teapot")


def fake_size(price, kind=Product.Kind.TEA, grams=50):
    """A size-like object for pure pricing tests."""
    return SimpleNamespace(price=Decimal(price), product=SimpleNamespace(kind=kind, name="X"), name="x",
                           net_grams=grams, package="pouch", shipping_grams=None,
                           shipping_weight=lambda: grams + 15)


def form_data(**extra):
    """POST data for a protected form, stamped well in the past."""
    return {protection.STAMP_FIELD: protection.form_stamp(time.time() - 60), **extra}


def checkout_to_payment(client, size, quantity=1, address=None, rate_index=0):
    """Add size to the cart and go through address and shipping; returns
    the shipping step's response (a redirect to the pay page)."""
    client.post("/cart/add/", {"size": size.pk, "quantity": quantity})
    client.post("/checkout/", form_data(**(address or ADDRESS)))
    page = client.get("/checkout/shipping/")
    rate = page.context["options"][rate_index][0]
    return client.post("/checkout/shipping/", {"rate": rate.id})
