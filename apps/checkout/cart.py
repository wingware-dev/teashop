"""The visitor's cart, kept in the database and found through the session."""

from django.conf import settings
from django.db import transaction

from .models import Cart, CartLine

SESSION_KEY = "checkout_cart_id"


def get_cart(request, create=False):
    """The visitor's cart, or None (or a new one, with create)."""
    from .accounts import current_customer

    cart_id = request.session.get(SESSION_KEY)
    cart = Cart.objects.filter(pk=cart_id).first() if cart_id else None
    if cart is None and create:
        cart = Cart.objects.create(customer=current_customer(request))
        request.session[SESSION_KEY] = cart.pk
    return cart


def forget_cart(request):
    request.session.pop(SESSION_KEY, None)


def sellable(size):
    return size.is_active and size.product.is_active


def cart_lines(cart):
    """The cart's lines with their size options and products loaded."""
    if cart is None:
        return []
    return list(cart.lines.select_related("size_option__product__category", "size_option__product__tea"))


def cart_items(cart):
    """[(size option, quantity)] for the sizes still on sale."""
    return [(line.size_option, line.quantity) for line in cart_lines(cart) if sellable(line.size_option)]


def problems(cart):
    """What stops the cart being ordered as it is: sizes no longer sold,
    or more than are in stock.  [(line, message)]."""
    found = []
    for line in cart_lines(cart):
        size = line.size_option
        if not sellable(size):
            found.append((line, f"{size.product.name}, {size.name} is no longer sold; please remove it."))
            continue
        available = size.packages_available()
        if available <= 0:
            found.append((line, f"{size.product.name}, {size.name} has sold out; please remove it."))
        elif line.quantity > available:
            found.append((line, f"Only {available} of {size.product.name}, {size.name} left; "
                                f"please lower the quantity."))
    return found


@transaction.atomic
def add(cart, size, quantity):
    """Add quantity of size; returns (quantity now in the cart, message
    for the customer if less was added than asked)."""
    if not sellable(size):
        return 0, "This size is not for sale."
    line = CartLine.objects.select_for_update().filter(cart=cart, size_option=size).first()
    if line is None and cart.lines.count() >= settings.CART_MAX_LINES:
        return 0, "Your cart is full.  Please check out or remove something first."
    current = line.quantity if line else 0
    wanted = current + max(1, quantity)
    limit = min(settings.CART_MAX_QUANTITY, size.packages_available())
    message = ""
    if wanted > limit:
        wanted = limit
        message = (f"Only {limit} of these can be ordered at a time." if limit == settings.CART_MAX_QUANTITY
                   else f"We have {limit} of these in stock." if limit else "Sorry, this has sold out.")
    if wanted <= 0:
        return current, message
    if line:
        line.quantity = wanted
        line.save(update_fields=["quantity"])
    else:
        CartLine.objects.create(cart=cart, size_option=size, quantity=wanted)
    cart.save(update_fields=["updated_at"])
    return wanted, message


@transaction.atomic
def set_quantity(cart, line_id, quantity):
    """Change a line's quantity (0 removes it); returns a message if it
    was limited."""
    line = CartLine.objects.select_for_update().filter(cart=cart, pk=line_id).select_related(
        "size_option__product").first()
    if line is None:
        return ""
    if quantity <= 0:
        line.delete()
        return ""
    limit = min(settings.CART_MAX_QUANTITY, line.size_option.packages_available())
    message = ""
    if quantity > limit:
        quantity = max(limit, 1)
        message = f"{line.size_option.product.name}: at most {quantity} can be ordered now."
    line.quantity = quantity
    line.save(update_fields=["quantity"])
    cart.save(update_fields=["updated_at"])
    return message


def merge_items(cart, items):
    """Add [(size, quantity)] (buy again); returns messages for what could
    not be added in full."""
    messages = []
    for size, quantity in items:
        added, message = add(cart, size, quantity)
        if message:
            messages.append(f"{size.product.name}, {size.name}: {message}")
    return messages
