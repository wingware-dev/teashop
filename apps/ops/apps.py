from datetime import timedelta

from django.apps import AppConfig


class OpsConfig(AppConfig):
    name = "apps.ops"
    label = "ops"
    verbose_name = "Server operations and security"

    def ready(self):
        from apps.audit.ops import OpsKind, register_kind
        from apps.core import attention

        from . import alerts

        # On the dashboard's Operations card, next to deploys and backups.
        # Unchanged health results are recorded once a day (agent.py).
        register_kind(OpsKind("health_check", "Server health check", "ops agent",
                              expected_every=timedelta(hours=26)))
        register_kind(OpsKind("upkeep", "Server upkeep (updates, logs)", "ops agent",
                              expected_every=timedelta(days=2)))
        register_kind(OpsKind("quarterly_review", "Quarterly security review", "owner",
                              expected_every=timedelta(days=100)))
        attention.register(alerts.attention_items)
        attention.register_shortcut("Server health and security", "ops:owner_home")
