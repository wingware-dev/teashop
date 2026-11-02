"""The owner dashboard's "Needs your attention" list.

core depends on no feature app, so feature apps register a provider in
their AppConfig.ready()::

    from apps.core import attention
    attention.register(my_provider)

A provider takes no arguments and returns a list of Attention items.  A
provider that fails is logged and skipped, so one broken app cannot take
the dashboard down.

Apps add links to the dashboard's Shortcuts card the same way, with
register_shortcut(title, url_name).
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


# Links for the dashboard's Shortcuts card, as (title, URL name), so feature
# apps can add their back-office pages without core naming them.
_shortcuts = []


def register_shortcut(title, url_name):
    if (title, url_name) not in _shortcuts:
        _shortcuts.append((title, url_name))


def shortcuts():
    """[(title, url)] for the registered shortcuts."""
    from django.urls import NoReverseMatch, reverse

    links = []
    for title, url_name in _shortcuts:
        try:
            links.append((title, reverse(url_name)))
        except NoReverseMatch:
            log.exception("Dashboard shortcut %r has no URL %r", title, url_name)
    return links
