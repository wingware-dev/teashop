from django.apps import AppConfig


class ReportsConfig(AppConfig):
    name = "apps.reports"
    label = "reports"
    verbose_name = "Reports and accounting"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        attention.register_shortcut("Sales by period, product, category and channel", "reports:sales")
        attention.register_shortcut("Cost of goods, margin, stock value and loss", "reports:margin")
        attention.register_shortcut("New York sales tax return", "reports:sales_tax")
        attention.register_shortcut("Quarterly estimated income tax", "reports:estimated_tax")
        attention.register_shortcut("Daily summaries sent to Wave", "reports:accounting")
