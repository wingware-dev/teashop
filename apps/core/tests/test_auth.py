"""The owner login: password plus authenticator code, admin behind it, and
lockout after repeated failures."""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.core.testing import OWNER_PASSWORD, current_token, login_verified, make_owner

LOGIN_URL = reverse("two_factor:login")
ADMIN_INDEX = "/" + settings.ADMIN_URL


def auth_step(username, password):
    return {"login_view-current_step": "auth", "auth-username": username, "auth-password": password}


def token_step(token):
    return {"login_view-current_step": "token", "token-otp_token": token}


class TwoFactorLoginTests(TestCase):
    def setUp(self):
        self.owner, self.device = make_owner()

    def test_full_login_needs_password_then_code(self):
        response = self.client.post(LOGIN_URL, auth_step("owner", OWNER_PASSWORD))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "token-otp_token")  # now asks for the code

        response = self.client.post(LOGIN_URL, token_step(current_token(self.device)))
        self.assertRedirects(response, reverse("core:owner_dashboard"))
        self.assertEqual(self.client.get(reverse("core:owner_dashboard")).status_code, 200)

    def test_wrong_code_is_refused(self):
        self.client.post(LOGIN_URL, auth_step("owner", OWNER_PASSWORD))
        good = current_token(self.device)
        bad = f"{(int(good) + 1) % 1000000:06d}"
        response = self.client.post(LOGIN_URL, token_step(bad))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "token-otp_token")
        self.assertEqual(self.client.get(reverse("core:owner_dashboard")).status_code, 302)

    def test_wrong_password_never_reaches_code_step(self):
        response = self.client.post(LOGIN_URL, auth_step("owner", "not-the-password"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "token-otp_token")

    def test_login_page_renders_with_site_template(self):
        response = self.client.get(LOGIN_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "css/site.css")
        self.assertNotContains(response, "bootstrap")


class AdminRequiresTwoFactorTests(TestCase):
    def test_admin_redirects_password_only_session_to_two_factor_login(self):
        owner, _device = make_owner()
        self.client.force_login(owner)
        response = self.client.get(ADMIN_INDEX)
        self.assertEqual(response.status_code, 302)
        login = self.client.get(response["Location"], follow=True)
        self.assertEqual(login.request["PATH_INFO"], LOGIN_URL)

    def test_admin_open_after_two_factor(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        response = self.client.get(ADMIN_INDEX)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audit log")


class BruteForceLockoutTests(TestCase):
    def test_lockout_after_repeated_failures_blocks_even_right_password(self):
        make_owner()
        limit = settings.AXES_FAILURE_LIMIT
        for _ in range(limit - 1):
            response = self.client.post(LOGIN_URL, auth_step("owner", "wrong-password"))
            self.assertEqual(response.status_code, 200)
        response = self.client.post(LOGIN_URL, auth_step("owner", "wrong-password"))
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Too many sign-in attempts", status_code=429)

        response = self.client.post(LOGIN_URL, auth_step("owner", OWNER_PASSWORD))
        self.assertEqual(response.status_code, 429)
