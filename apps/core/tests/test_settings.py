"""Production settings, checked in a fresh process since settings load once."""

import os
import subprocess
import sys
from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]

PRODUCTION_ENV = {
    "DJANGO_ENV": "production",
    "DJANGO_SECRET_KEY": "test-only-" + "x" * 50,
    "DATABASE_URL": "sqlite:////tmp/teashop-settings-test.sqlite3",
    "DJANGO_ALLOWED_HOSTS": "shop.example.com",
    "DJANGO_CSRF_TRUSTED_ORIGINS": "https://shop.example.com",
    "DJANGO_ADMIN_URL": "office/",
}

# A deploy ready to take orders (apps/checkout/checks.py warns about each).
CHECKOUT_ENV = {
    "EMAIL_HOST": "smtp.example.com",
    "STRIPE_SECRET_KEY": "sk_test_settings",
    "STRIPE_PUBLISHABLE_KEY": "pk_test_settings",
    "STRIPE_WEBHOOK_SECRET": "whsec_settings",
    "EASYPOST_API_KEY": "EZTKsettings",
    "SHIP_FROM_STREET1": "1 Main St",
    "SHIP_FROM_CITY": "Albany",
    "SHIP_FROM_STATE": "NY",
    "SHIP_FROM_ZIP": "12207",
    "SHOP_POSTAL_ADDRESS": "PO Box 1\\nAlbany, NY 12207",
    "SITE_URL": "https://shop.example.com",
}
# Settings in the developer's own shell that would change the results.
INHERITED_ENV_EXCLUDED = ("DJANGO_", "DATABASE_URL", "SENTRY_", "EMAIL_", "STRIPE_", "EASYPOST_", "SHIP_FROM_",
                          "SHOP_POSTAL_ADDRESS", "SITE_URL", "PAYMENT_PROVIDER", "SHIPPING_PROVIDER")


def run_manage(*args, env):
    base = {k: v for k, v in os.environ.items() if not k.startswith(INHERITED_ENV_EXCLUDED)}
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=ROOT,
        env={**base, **env},
        capture_output=True,
        text=True,
        timeout=120,
    )


class ProductionSettingsTests(SimpleTestCase):
    def test_deploy_checks_pass(self):
        result = run_manage("check", "--deploy", "--fail-level", "WARNING", env={**PRODUCTION_ENV, **CHECKOUT_ENV})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_deploy_checks_warn_when_checkout_is_not_set_up(self):
        result = run_manage("check", "--deploy", "--fail-level", "WARNING", env=PRODUCTION_ENV)
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        for check_id in ("W001", "W002", "W004", "W005", "W006"):
            self.assertIn(f"checkout.{check_id}", output)
        self.assertNotIn("checkout.W003", output)  # only once Stripe is set up

    def test_deploy_checks_warn_without_stripe_webhook_secret(self):
        env = {k: v for k, v in {**PRODUCTION_ENV, **CHECKOUT_ENV}.items() if k != "STRIPE_WEBHOOK_SECRET"}
        result = run_manage("check", "--deploy", "--fail-level", "WARNING", env=env)
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn("checkout.W003", output)
        self.assertNotIn("checkout.W002", output)

    def test_missing_secret_key_refuses_to_start(self):
        env = {k: v for k, v in PRODUCTION_ENV.items() if k != "DJANGO_SECRET_KEY"}
        result = run_manage("check", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be set", result.stderr)

    def test_missing_database_url_refuses_to_start(self):
        env = {k: v for k, v in PRODUCTION_ENV.items() if k != "DATABASE_URL"}
        result = run_manage("check", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DATABASE_URL must be set", result.stderr)

    def test_debug_cannot_be_turned_on(self):
        result = run_manage("check", env={**PRODUCTION_ENV, "DJANGO_DEBUG": "1"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_DEBUG must not be on", result.stderr)
