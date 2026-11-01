from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = "apps.inventory"
    label = "inventory"
    verbose_name = "Inventory"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
