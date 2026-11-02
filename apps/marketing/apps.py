from django.apps import AppConfig


class MarketingConfig(AppConfig):
    name = "apps.marketing"
    label = "marketing"
    verbose_name = "Marketing"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        attention.register_shortcut("Marketing: ideas, posts and calendar", "marketing:home")
