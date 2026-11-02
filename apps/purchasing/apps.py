from django.apps import AppConfig


class PurchasingConfig(AppConfig):
    name = "apps.purchasing"
    label = "purchasing"
    verbose_name = "Purchasing and stock counts"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        attention.register_shortcut("Reorder: suggested purchase orders", "purchasing:reorder")
        attention.register_shortcut("Losses and samples by month", "purchasing:losses")
        attention.register_shortcut("Profit per tea and per size", "purchasing:profit")
