"""The cart and the checkout: cart → address → shipping → pay → done.

Each step is a plain page with a form (no JavaScript needed until the
payment fields, which are Stripe's).  The checkout's progress is kept in
the session (orders.CheckoutState).  While the shop is closed only the
signed-in owner gets here, as with the rest of the shop.
"""

import logging
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.catalog.models import SizeOption
from apps.storefront.browsing import shop_is_visible

from . import cart as carts
from . import payments, protection, shipping
from .accounts import current_customer
from .forms import AddressForm, DiscountForm
from .models import CheckoutSettings, DiscountCode, Order
from .orders import CheckoutState, OrderError, build_order, mark_paid, start_payment
from .pricing import quote
from .tax import TaxError

log = logging.getLogger(__name__)


def checkout_open():
    """None if orders can be taken now, else why not (for customers)."""
    if not (payments.is_configured() and shipping.is_configured()):
        return "Online ordering opens soon."
    if not CheckoutSettings.current().taking_orders():
        message = CheckoutSettings.current().vacation_message
        return message or "We are away and not taking orders just now.  Please come back soon."
    return None


def shop_view(view):
    """Only while the shop is visible to this visitor; else a 404."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not shop_is_visible(request):
            raise Http404("The shop is not open yet")
        return view(request, *args, **kwargs)

    return wrapper


def checkout_step(view):
    """A checkout step: the shop must be visible and taking orders, and the
    cart must have something in it."""

    @shop_view
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        closed = checkout_open()
        if closed:
            return render(request, "checkout/closed.html", {"reason": closed})
        cart = carts.get_cart(request)
        if cart is None or not cart.lines.exists():
            messages.info(request, "Your cart is empty.")
            return redirect("checkout:cart")
        return view(request, cart, *args, **kwargs)

    return wrapper


def _progress(step):
    steps = [("cart", "Cart"), ("address", "Address"), ("shipping", "Shipping"), ("pay", "Payment")]
    return [(key, label, key == step) for key, label in steps]


# -- Cart ---------------------------------------------------------------------

@shop_view
@require_GET
def cart_page(request):
    cart = carts.get_cart(request)
    items = carts.cart_items(cart)
    figures = quote(items, discount=cart.discount if cart else None)
    if cart and figures.discount_problem:
        messages.warning(request, figures.discount_problem)
    problems = {line.pk: message for line, message in carts.problems(cart)}
    rows = [{"line": line, "size": line.size_option, "total": line.size_option.price * line.quantity,
             "problem": problems.get(line.pk, "")} for line in carts.cart_lines(cart)]
    return render(request, "checkout/cart.html", {
        "cart": cart, "rows": rows, "figures": figures, "problems": problems,
        "closed": checkout_open(), "progress": _progress("cart"),
        "quantity_choices": range(1, settings.CART_MAX_QUANTITY + 1), **protection.context(),
    })


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@shop_view
@require_POST
def cart_add(request):
    size = SizeOption.objects.select_related("product").filter(pk=_int(request.POST.get("size"))).first()
    if size is None or not carts.sellable(size):
        messages.error(request, "Please choose a size.")
        return redirect(request.POST.get("next") or "checkout:cart")
    quantity = max(1, min(_int(request.POST.get("quantity"), 1), settings.CART_MAX_QUANTITY))
    cart = carts.get_cart(request, create=True)
    now_in_cart, message = carts.add(cart, size, quantity)
    if now_in_cart:
        messages.success(request, f"{size.product.name}, {size.name}: {now_in_cart} in your cart.")
    if message:
        messages.warning(request, message)
    return redirect("checkout:cart")


@shop_view
@require_POST
def cart_update(request):
    cart = carts.get_cart(request)
    if cart is None:
        return redirect("checkout:cart")
    if "remove" in request.POST:
        carts.set_quantity(cart, _int(request.POST.get("remove")), 0)
        messages.success(request, "Removed from your cart.")
    else:
        for line in cart.lines.all():
            field = f"quantity-{line.pk}"
            if field in request.POST:
                message = carts.set_quantity(cart, line.pk, _int(request.POST.get(field), line.quantity))
                if message:
                    messages.warning(request, message)
        messages.success(request, "Cart updated.")
    return redirect("checkout:cart")


@shop_view
@require_POST
def cart_discount(request):
    cart = carts.get_cart(request)
    if cart is None:
        return redirect("checkout:cart")
    if "remove" in request.POST:
        cart.discount = None
        cart.save(update_fields=["discount"])
        messages.success(request, "Discount code removed.")
        return redirect("checkout:cart")
    refused = protection.check(request, "discount")
    if refused:
        messages.error(request, refused)
        return redirect("checkout:cart")
    form = DiscountForm(request.POST)  # the cart page renders its one field by hand
    if not form.is_valid():
        messages.error(request, "Enter a discount code.")
        return redirect("checkout:cart")
    code = DiscountCode.objects.filter(code=form.cleaned_data["code"]).first()
    if code is None:
        messages.error(request, f"There is no discount code {form.cleaned_data['code']}.")
        return redirect("checkout:cart")
    problem = code.problem(quote(carts.cart_items(cart)).subtotal)
    if problem:
        messages.error(request, problem)
        return redirect("checkout:cart")
    cart.discount = code
    cart.save(update_fields=["discount"])
    messages.success(request, f"Discount code {code.code} applied.")
    return redirect("checkout:cart")


# -- Address ------------------------------------------------------------------

@checkout_step
@require_http_methods(["GET", "POST"])
def address_step(request, cart):
    state = CheckoutState.load(request)
    customer = current_customer(request)
    suggestion = None
    if request.method == "POST":
        form = AddressForm(request.POST)
        refused = protection.check(request, "checkout")
        if refused:
            messages.error(request, refused)
        elif form.is_valid():
            entered = form.address()
            choice = request.POST.get("use")
            if choice == "entered" and state.address and shipping.Address(**state.address) == entered:
                # The customer kept their own spelling of an address the
                # checker suggested changing: accept it, unverified.
                return _address_done(request, state, form.cleaned_data["email"], entered, verified=False)
            try:
                checked = shipping.provider().verify(entered)
            except shipping.ShippingError as exc:
                messages.error(request, str(exc))
            else:
                if choice == "suggested" and checked.ok:
                    return _address_done(request, state, form.cleaned_data["email"], checked.address, True)
                if checked.ok and not checked.changed_from(entered):
                    return _address_done(request, state, form.cleaned_data["email"], checked.address, True)
                state.email, state.address = form.cleaned_data["email"], entered.as_dict()
                state.save(request)
                suggestion = checked
                if not checked.ok:
                    for message in checked.messages:
                        form.add_error(None, message)
    else:
        initial = AddressForm.initial_from(state.email or (customer.email if customer else ""),
                                           state.ship_to or (customer.address if customer and customer.has_address
                                                             else None))
        form = AddressForm(initial=initial)
    return render(request, "checkout/address.html", {
        "form": form, "suggestion": suggestion, "progress": _progress("address"), "customer": customer,
        **protection.context(),
    })


def _address_done(request, state, email, address, verified):
    state.email = email.strip().lower()
    state.address = address.as_dict()
    state.address_verified = verified
    state.rates = []
    state.save(request)
    customer = current_customer(request)
    if customer and request.POST.get("save_address"):
        customer.set_address(address)
        customer.save()
    return redirect("checkout:shipping")


# -- Shipping -----------------------------------------------------------------

@checkout_step
@require_http_methods(["GET", "POST"])
def shipping_step(request, cart):
    state = CheckoutState.load(request)
    if not state.address:
        return redirect("checkout:address")
    items = carts.cart_items(cart)
    if not state.rates:
        try:
            rates = shipping.provider().rates(state.ship_to, shipping.parcel_grams(items))
        except shipping.ShippingError as exc:
            messages.error(request, str(exc))
            return redirect("checkout:address")
        state.set_rates(rates)
        state.save(request)
    rates = state.rate_list()
    if request.method == "POST":
        if request.POST.get("rate") in {rate.id for rate in rates}:
            state.rate_id = request.POST["rate"]
            state.save(request)
        else:
            messages.error(request, "Choose a shipping service.")
            return redirect("checkout:shipping")
        try:
            order = build_order(cart, state, current_customer(request))
        except (OrderError, TaxError) as exc:
            messages.error(request, str(exc))
            return redirect("checkout:cart" if isinstance(exc, OrderError) else "checkout:shipping")
        state.save(request)
        return redirect("checkout:pay")
    try:
        options = [(rate, quote(items, discount=cart.discount, email=state.email, rates=rates, rate=rate))
                   for rate in rates]
        chosen = quote(items, discount=cart.discount, email=state.email, rates=rates, rate=state.chosen_rate(),
                       address=state.ship_to)
    except TaxError as exc:
        messages.error(request, str(exc))
        return redirect("checkout:address")
    return render(request, "checkout/shipping.html", {
        "options": options, "state": state, "figures": chosen, "progress": _progress("shipping"),
        "ship_by": CheckoutSettings.current().ship_by(), "settings_obj": CheckoutSettings.current(),
    })


# -- Payment ------------------------------------------------------------------

def _pending_order(request):
    state = CheckoutState.load(request)
    if not state.order_id:
        return None
    return Order.objects.filter(pk=state.order_id, status=Order.Status.PENDING).first()


@checkout_step
@require_GET
def pay_step(request, cart):
    order = _pending_order(request)
    if order is None:
        return redirect("checkout:shipping")
    try:
        started = start_payment(order)
    except payments.PaymentError as exc:
        messages.error(request, str(exc))
        return redirect("checkout:shipping")
    provider = payments.provider()
    return render(request, "checkout/pay.html", {
        "order": order, "lines": list(order.lines.all()), "progress": _progress("pay"),
        "provider": provider.name, "publishable_key": provider.publishable_key, "client_secret": started.client_secret,
        "return_url": request.build_absolute_uri(reverse("checkout:complete")),
        "pay_label": f"Pay ${order.total:,.2f}", "fake_action": reverse("checkout:fake_pay"),
    })


@shop_view
@require_POST
def fake_pay(request):
    """The stand-in payment's button (laptops and tests only)."""
    if payments.provider().name != "fake":
        raise Http404("Not available")
    order = _pending_order(request)
    if order is None:
        return redirect("checkout:cart")
    mark_paid(order, order.total)
    return _finish(request, order)


@shop_view
@require_GET
def complete(request):
    """Where Stripe sends the customer after paying (return_url)."""
    order = _pending_order(request)
    payment_id = request.GET.get("payment_intent", "")
    if order is None and payment_id:
        order = Order.objects.filter(payment_id=payment_id).first()
    if order is None:
        return redirect("checkout:cart")
    if not order.is_paid and order.payment_id == payment_id:
        status, received = payments.provider().payment_status(payment_id)
        if status == "succeeded":
            mark_paid(order, received)
        elif status in ("requires_payment_method", "canceled"):
            messages.error(request, "The payment did not go through.  Please try again or use another way to pay.")
            return redirect("checkout:pay")
    return _finish(request, order)


def _finish(request, order):
    CheckoutState.clear(request)
    carts.forget_cart(request)
    request.session["checkout_just_ordered"] = order.token
    return redirect(order.get_absolute_url())


@require_GET
def order_status(request, token):
    """The customer's order page (the link in their emails); the token is
    the secret, so no sign-in is needed."""
    order = get_object_or_404(Order, token=token)
    just_ordered = request.session.pop("checkout_just_ordered", None) == token
    return render(request, "checkout/order.html", {"order": order, "lines": list(order.lines.all()),
                                                    "just_ordered": just_ordered})
