from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = "apps.inventory"
    label = "inventory"
    verbose_name = "Inventory"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        group = "Stock: receiving, lots and suppliers"
        attention.register_shortcut("Receive a delivery (new lots)", "admin:inventory_receipt_add", group)
        attention.register_shortcut("Lots in stock", "admin:inventory_lot_changelist", group)
        attention.register_shortcut("Stock items: teas, ingredients and supplies", "admin:inventory_item_changelist", group)
        attention.register_shortcut("Purchase orders", "admin:inventory_purchaseorder_changelist", group)
        attention.register_shortcut("Suppliers", "admin:inventory_supplier_changelist", group)
        group = "Packaging and shipping supplies"
        attention.register_shortcut("Packaging: pouches, tins, labels", "admin:inventory_item_changelist", group,
                                    query="kind__exact=packaging")
        attention.register_shortcut("Shipping boxes and mailers (stock)", "admin:inventory_item_changelist", group,
                                    query="kind__exact=shipping_box")
