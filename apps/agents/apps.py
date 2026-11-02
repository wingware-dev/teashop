from django.apps import AppConfig


class AgentsConfig(AppConfig):
    name = "apps.agents"
    label = "agents"
    verbose_name = "AI agents"

    def ready(self):
        from apps.core import attention

        from . import alerts

        attention.register(alerts.attention_items)
        attention.register_shortcut("AI agents: spending and actions", "agents:owner_home")
