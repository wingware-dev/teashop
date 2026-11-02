from unittest import mock

from django.db.utils import OperationalError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.audit import record
from apps.core.testing import login_verified, make_owner


@override_settings(GIT_SHA="abc123")
class HealthCheckTests(TestCase):
    def test_ok_when_database_reachable(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok", "version": "abc123"})
        self.assertIn("no-cache", response["Cache-Control"])

    def test_503_when_database_unreachable(self):
        with mock.patch("apps.core.views.connection.cursor", side_effect=OperationalError("down")):
            with self.assertLogs("apps.core.views", level="ERROR") as logs:
                response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("database unreachable", logs.output[0])


class OwnerDashboardTests(TestCase):
    url = reverse("core:owner_dashboard")

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("two_factor:login")))

    def test_password_only_login_is_not_enough(self):
        owner, _device = make_owner()
        self.client.force_login(owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("two_factor:login")))

    def test_new_owner_without_authenticator_is_sent_to_setup(self):
        owner, device = make_owner()
        device.delete()
        self.client.force_login(owner)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("two_factor:setup"))
        setup = self.client.get(response["Location"])
        self.assertEqual(setup.status_code, 200)
        self.assertContains(setup, "css/site.css")

    def test_verified_non_staff_user_is_refused(self):
        user, device = make_owner(username="customer", staff=False, superuser=False)
        login_verified(self.client, user, device)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_verified_owner_sees_dashboard_and_recent_activity(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        record("ops.test_event", message="Backup restore test passed")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Needs your attention")
        self.assertContains(response, "ops.test_event")
        self.assertContains(response, "Backup restore test passed")

    def test_dashboard_links_the_back_office_setup_pages_in_groups(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        response = self.client.get(self.url)
        for group in ("Catalog: teas and goods", "Stock: receiving, lots and suppliers",
                      "Packaging and shipping supplies"):
            self.assertContains(response, f'<h3 class="shortcut-group">{group}</h3>', html=True)
        for name in ("catalog_product_changelist", "inventory_receipt_add", "inventory_supplier_changelist",
                     "purchasing_stockcount_changelist", "fulfillment_boxsize_changelist",
                     "fulfillment_scale_changelist"):
            self.assertContains(response, f'href="{reverse("admin:" + name)}"')
        self.assertContains(response, reverse("admin:inventory_item_changelist") + "?kind__exact=packaging")

    def test_logout_ends_session(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        response = self.client.post(reverse("core:logout"))
        self.assertRedirects(response, reverse("storefront:home"))
        self.assertEqual(self.client.get(self.url).status_code, 302)
