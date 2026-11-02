"""The report pages, behind the owner's two-factor sign-in."""

from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.testing import login_verified, make_owner

from .helpers import order, refund

PAGES = ["reports:sales", "reports:margin", "reports:sales_tax", "reports:estimated_tax", "reports:accounting"]


class ReportPageTests(TestCase):
    def setUp(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        now = timezone.now()
        made = order(now - timedelta(days=1), tea="20.00", goods="40.00", shipping="6.00", tax="3.20",
                     jurisdiction="Albany County", rate="0.08")
        refund(made, "5.00", now)

    def test_pages_need_the_owner(self):
        self.client.logout()
        for name in PAGES:
            self.assertEqual(self.client.get(reverse(name)).status_code, 302, name)

    def test_pages_show_their_figures(self):
        self.assertContains(self.client.get(reverse("reports:sales")), "Teapot")
        self.assertContains(self.client.get(reverse("reports:sales") + "?by=week&start=2026-01-01"), "Week of")
        self.assertContains(self.client.get(reverse("reports:margin")), "Gross margin")
        page = self.client.get(reverse("reports:sales_tax"))
        self.assertContains(page, "Albany County")
        self.assertContains(self.client.get(reverse("reports:sales_tax") + "?annual=1"), "Whole year")
        self.assertContains(self.client.get(reverse("reports:estimated_tax") + "?year=x"), "1040-ES")
        self.assertContains(self.client.get(reverse("reports:accounting")), "Not connected to Wave yet")

    def test_bad_dates_fall_back(self):
        page = self.client.get(reverse("reports:sales") + "?start=nope&end=2026-13-40&by=fortnight")
        self.assertEqual(page.status_code, 200)

    def test_send_now_queues_the_job(self):
        with mock.patch("apps.reports.jobs.accounting_summary.enqueue") as enqueue:
            response = self.client.post(reverse("reports:accounting"))
        self.assertRedirects(response, reverse("reports:accounting"))
        enqueue.assert_called_once_with()

    def test_dashboard_lists_the_report_shortcuts(self):
        page = self.client.get(reverse("core:owner_dashboard"))
        self.assertContains(page, reverse("reports:sales_tax"))
