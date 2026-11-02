from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class JobsConfig(AppConfig):
    name = "apps.jobs"
    label = "jobs"
    verbose_name = "Background jobs"

    def ready(self):
        from apps.core import attention

        from . import alerts, queue  # noqa: F401 (queue declares the purge schedule)

        attention.register(alerts.attention_items)
        # Each app declares its periodic jobs in its jobs.py.
        autodiscover_modules("jobs")
