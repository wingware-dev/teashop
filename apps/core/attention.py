"""The owner dashboard's "Needs your attention" list.

core depends on no feature app, so feature apps register a provider in
their AppConfig.ready()::

    from apps.core import attention
    attention.register(my_provider)

A provider takes no arguments and returns a list of Attention items.  A
provider that fails is logged and skipped, so one broken app cannot take
the dashboard down.
"""

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

_providers = []


@dataclass(frozen=True)
class Attention:
    title: str
    detail: str = ""
    url: str = ""
    # "warning" for things to act on soon, "urgent" for things to act on now.
    level: str = "warning"


def register(provider):
    if provider not in _providers:
        _providers.append(provider)


def collect():
    items = []
    for provider in _providers:
        try:
            items.extend(provider())
        except Exception:
            log.exception("Attention provider %r failed", provider)
    items.sort(key=lambda item: item.level != "urgent")
    return items
