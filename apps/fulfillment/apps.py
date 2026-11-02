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
        group = "Packaging and shipping supplies"
        attention.register_shortcut("Box sizes", "admin:fulfillment_boxsize_changelist", group)
        attention.register_shortcut("Package dimensions per size", "admin:fulfillment_packagedimensions_changelist",
                                    group)
        attention.register_shortcut("Scales", "admin:fulfillment_scale_changelist", group)
