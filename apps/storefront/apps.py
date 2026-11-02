from django.apps import AppConfig


class StorefrontConfig(AppConfig):
    name = "apps.storefront"
    label = "storefront"
    verbose_name = "Storefront"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        attention.register_shortcut("Page designs to approve", "storefront:variant_list")
