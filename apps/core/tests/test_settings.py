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


def run_manage(*args, env):
    base = {k: v for k, v in os.environ.items() if not k.startswith(("DJANGO_", "DATABASE_URL", "SENTRY_"))}
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
        result = run_manage("check", "--deploy", "--fail-level", "WARNING", env=PRODUCTION_ENV)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
