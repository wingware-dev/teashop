"""What every page's header needs from checkout: the cart's count, whether
a customer is signed in, and the vacation notice."""

import logging

from django.db import DatabaseError

log = logging.getLogger(__name__)


def checkout(request):
    from .accounts import current_customer
    from .cart import get_cart
    from .models import CheckoutSettings

    from django.conf import settings

    context = {"cart_count": 0, "customer": None, "vacation_notice": "", "ordering_closed": "",
               "contact_email": settings.SHOP_CONTACT_EMAIL, "postal_address": settings.SHOP_POSTAL_ADDRESS}
    try:
        cart = get_cart(request) if hasattr(request, "session") else None
        context["cart_count"] = cart.item_count() if cart else 0
        context["customer"] = current_customer(request) if hasattr(request, "session") else None
        from .views import checkout_open

        context["ordering_closed"] = checkout_open() or ""
        shop = CheckoutSettings.current()
        if shop.on_vacation():
            context["vacation_notice"] = shop.vacation_message or (
                f"We are away: orders ship from {shop.vacation_ships_from:%B} {shop.vacation_ships_from.day}."
                if shop.vacation_ships_from else "We are away for a little while.")
    except DatabaseError:
        # Error pages render with this too; a database outage must not
        # turn them into a second error.
        log.exception("Checkout header information unavailable")
    return context
