from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("sales/", views.sales_report, name="sales"),
    path("margin/", views.margin_report, name="margin"),
    path("sales-tax/", views.sales_tax_report, name="sales_tax"),
    path("estimated-tax/", views.estimated_tax_report, name="estimated_tax"),
    path("accounting/", views.accounting_report, name="accounting"),
]
