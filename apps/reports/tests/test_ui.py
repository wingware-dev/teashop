"""The report pages and the dashboard's queue in a real browser: phone and
desktop, light and dark, WCAG 2.2 AA checks, screenshots (see
apps.core.uitesting)."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.core.uitesting import BrowserTestCase
from apps.inventory.models import PurchaseOrder, Supplier
from apps.reports import accounting

from .helpers import order, refund


def sample_sales():
    now = timezone.now()
    for days, figures in enumerate([
        dict(tea="32.00", shipping="5.40", fee="1.29", jurisdiction="Albany County", rate="0.08"),
        dict(tea="18.00", goods="42.00", shipping="7.10", tax="3.93", fee="2.18", jurisdiction="Albany County",
             rate="0.08"),
        dict(goods="28.00", shipping="6.20", tax="2.79", fee="1.29", jurisdiction="New York City", rate="0.08875"),
        dict(tea="24.00", state="NJ", fee="1.00"),
    ]):
        made = order(now - timedelta(days=days * 9 + 1), **figures)
    refund(made, "6.00", now - timedelta(hours=3))
    for days in (1, 2, 3):
        accounting.post_day(timezone.localdate() - timedelta(days=days * 9))


class ReportsUITests(BrowserTestCase):
    def test_sales(self):
        sample_sales()
        self.check_page(reverse("reports:sales"), "reports-sales", signed_in=True)

    def test_margin(self):
        sample_sales()
        self.check_page(reverse("reports:margin"), "reports-margin", signed_in=True)

    def test_sales_tax(self):
        sample_sales()
        self.check_page(reverse("reports:sales_tax"), "reports-sales-tax", signed_in=True)

    def test_estimated_tax(self):
        sample_sales()
        self.check_page(reverse("reports:estimated_tax"), "reports-estimated-tax", signed_in=True)

    def test_accounting(self):
        sample_sales()
        self.check_page(reverse("reports:accounting"), "reports-accounting", signed_in=True)

    def test_dashboard_queue(self):
        sample_sales()
        supplier = Supplier.objects.create(name="Leaf Importers")
        draft = PurchaseOrder.objects.create(supplier=supplier)
        PurchaseOrder.objects.filter(pk=draft.pk).update(created_at=timezone.now() - timedelta(days=3))
        self.check_page(reverse("core:owner_dashboard"), "owner-dashboard-queue", signed_in=True)
