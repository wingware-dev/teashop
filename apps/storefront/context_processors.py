"""What every page's header and footer need: the shop's name, its
navigation, and whether the visitor may see the shop yet."""

import logging

from django.conf import settings
from django.db import DatabaseError

from apps.catalog.models import Category, Collection

from .browsing import shop_is_visible

log = logging.getLogger(__name__)

# The apps whose pages customers see; their owner pages live under /owner/.
CUSTOMER_NAMESPACES = {"storefront", "checkout", "emaillist", "support", "fulfillment"}


def is_customer_page(request):
    """Whether the page is one customers see (shop, cart, checkout,
    account, policies, email list, chat), which wears the vine frame;
    the owner's back office and the staff sign-in keep the plain look."""
    match = getattr(request, "resolver_match", None)
    if match is None or request.path.startswith("/owner/"):
        return False
    return match.namespace in CUSTOMER_NAMESPACES


def storefront(request):
    context = {"shop_name": settings.SHOP_NAME, "shop_visible": False, "nav_teas": [], "nav_goods": [],
               "nav_collections": [], "vine_frame": is_customer_page(request)}
    if not shop_is_visible(request):
        return context
    context["shop_visible"] = True
    try:
        categories = list(Category.objects.filter(is_active=True))
        context["nav_teas"] = [c for c in categories if c.section == Category.Section.TEA]
        context["nav_goods"] = [c for c in categories if c.section == Category.Section.GOODS]
        context["nav_collections"] = list(Collection.objects.showing())
    except DatabaseError:
        # Error pages render with this too; a database outage must not
        # turn them into a second error.
        log.exception("Storefront navigation unavailable")
    return context
