from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "apps.catalog"
    label = "catalog"
    verbose_name = "Catalog"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        group = "Catalog: teas and goods"
        attention.register_shortcut("Teas and other products", "admin:catalog_product_changelist", group)
        attention.register_shortcut("Sizes, prices and SKUs", "admin:catalog_sizeoption_changelist", group)
        attention.register_shortcut("Categories", "admin:catalog_category_changelist", group)
        attention.register_shortcut("Collections", "admin:catalog_collection_changelist", group)
        attention.register_shortcut("Regions", "admin:catalog_region_changelist", group)
