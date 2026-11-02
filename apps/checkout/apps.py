from django.apps import AppConfig


class CheckoutConfig(AppConfig):
    name = "apps.checkout"
    label = "checkout"
    verbose_name = "Checkout and orders"

    def ready(self):
        from apps.core import attention

        from . import alerts, checks  # noqa: F401 (checks registers itself)

        attention.register(alerts.attention_items)
        attention.register_shortcut("Sales by state and sales tax", "checkout:sales_by_state")
