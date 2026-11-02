from django.apps import AppConfig


class FulfillmentConfig(AppConfig):
    name = "apps.fulfillment"
    label = "fulfillment"
    verbose_name = "Fulfillment"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        attention.register_shortcut("Orders to pack and ship", "fulfillment:queue")
        attention.register_shortcut("Packing list", "fulfillment:packing_list")
        attention.register_shortcut("USPS pickups", "fulfillment:pickups")
