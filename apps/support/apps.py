from django.apps import AppConfig


class SupportConfig(AppConfig):
    name = "apps.support"
    label = "support"
    verbose_name = "Customer support"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        attention.register_shortcut("Customer support", "support:owner_inbox")
