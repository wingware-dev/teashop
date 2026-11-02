from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "apps.audit"
    label = "audit"
    verbose_name = "Audit log"

    def ready(self):
        from apps.core import attention

        from . import alerts, signals

        signals.connect()
        attention.register(alerts.attention_items)
