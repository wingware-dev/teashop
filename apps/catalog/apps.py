from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "apps.catalog"
    label = "catalog"
    verbose_name = "Catalog"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
