from django.apps import AppConfig


class EmailListConfig(AppConfig):
    name = "apps.emaillist"
    label = "emaillist"
    verbose_name = "Email list"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        attention.register_shortcut("Email list and mailings", "emaillist:owner_home")
