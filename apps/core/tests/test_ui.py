"""The phase 1 pages in a real browser: phone and desktop, light and dark,
WCAG 2.2 AA checks, screenshots (see apps.core.uitesting)."""

from django.urls import reverse

from apps.audit import record
from apps.core.testing import OWNER_PASSWORD, make_owner
from apps.core.uitesting import BrowserTestCase


class PublicPagesUITests(BrowserTestCase):
    def test_home(self):
        self.check_page(reverse("core:home"), "home")


class OwnerLoginUITests(BrowserTestCase):
    def test_login_with_password_and_code_reaches_dashboard(self):
        for viewport in ("phone", "desktop"):
            for theme in ("light", "dark"):
                with self.subTest(viewport=viewport, theme=theme):
                    page = self.new_page(viewport, theme)
                    # Each login uses up its code, so each needs its own owner.
                    owner = make_owner(username=f"owner-{viewport}-{theme}")
                    self.sign_in_with_form(page, shot_prefix="login", owner=owner)
                    self.assertEqual(page.url, self.url(reverse("core:owner_dashboard")))
                    self.assertTrue(page.get_by_role("button", name="Log out").is_visible())

    def test_wrong_code_stays_on_code_step(self):
        user, device = self.owner()
        page = self.new_page()
        page.goto(self.url(reverse("two_factor:login")))
        page.get_by_label("Username").fill(user.username)
        page.get_by_label("Password").fill(OWNER_PASSWORD)
        page.get_by_role("button", name="Next").click()
        page.get_by_label("Token").fill("000000")
        page.get_by_role("button", name="Next").click()
        self.assertTrue(page.get_by_label("Token").is_visible())
        self.check_current(page, "login-wrong-code")


class OwnerPagesUITests(BrowserTestCase):
    def test_dashboard(self):
        record("ui.sample_event", message="Sample event so the audit table has a row")
        self.check_page(reverse("core:owner_dashboard"), "owner-dashboard", signed_in=True)

    def test_account_security(self):
        self.check_page(reverse("two_factor:profile"), "account-security", signed_in=True)

    def test_dashboard_needs_sign_in(self):
        page = self.new_page()
        page.goto(self.url(reverse("core:owner_dashboard")))
        self.assertTrue(page.url.startswith(self.url(reverse("two_factor:login"))))
