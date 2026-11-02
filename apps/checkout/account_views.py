"""Customer accounts: sign in with an emailed link, see orders and
subscriptions, buy again, cancel a subscription."""

from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import accounts, emails, protection
from . import cart as carts
from .forms import SignInForm
from .views import shop_view


def customer_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        customer = accounts.current_customer(request)
        if customer is None:
            return redirect("checkout:sign_in")
        return view(request, customer, *args, **kwargs)

    return wrapper


@shop_view
@require_http_methods(["GET", "POST"])
def sign_in(request):
    if request.method == "POST":
        form = SignInForm(request.POST)
        refused = protection.check(request, "sign-in", settings.SIGN_IN_RATE_LIMIT)
        if refused:
            messages.error(request, refused)
        elif form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            if not protection.over_limit(request, f"sign-in-email:{email}", settings.SIGN_IN_RATE_LIMIT):
                url = emails.absolute(reverse("checkout:sign_in_link", args=[accounts.sign_in_token(email)]))
                emails.sign_in_link(email, url)
            # The same answer whether or not the email has orders, so the
            # page can't be used to find out who shops here.
            return render(request, "checkout/account/link_sent.html", {"email": email})
    else:
        form = SignInForm()
    return render(request, "checkout/account/sign_in.html", {"form": form, **protection.context()})


@shop_view
@require_http_methods(["GET", "POST"])
def sign_in_link(request, token):
    """GET shows a button; only the POST signs in, so mail scanners that
    open links can't use up the one-time link."""
    if request.method == "POST":
        customer = accounts.redeem(token)
        if customer is None:
            messages.error(request, "That sign-in link has expired or was already used.  Ask for a new one.")
            return redirect("checkout:sign_in")
        accounts.sign_in(request, customer)
        messages.success(request, f"Signed in as {customer.email}.")
        return redirect("checkout:account")
    return render(request, "checkout/account/confirm_sign_in.html", {"token": token})


@shop_view
@require_POST
def sign_out(request):
    accounts.sign_out(request)
    messages.success(request, "Signed out.")
    return redirect("storefront:home")


@shop_view
@require_GET
@customer_required
def account(request, customer):
    orders = list(customer.orders().prefetch_related("lines")[:50])
    return render(request, "checkout/account/home.html", {
        "customer": customer, "orders": orders,
        "subscriptions": list(customer.subscriptions.exclude(status="pending").select_related("plan")),
    })


@shop_view
@require_POST
@customer_required
def buy_again(request, customer, number):
    order = get_object_or_404(customer.orders().filter(subscription=None), number=number)
    lines = list(order.lines.select_related("size_option__product"))
    items = [(line.size_option, line.quantity) for line in lines
             if line.size_option_id and carts.sellable(line.size_option)]
    cart = carts.get_cart(request, create=True)
    for problem in carts.merge_items(cart, items):
        messages.warning(request, problem)
    missing = len(lines) - len(items)
    if missing:
        messages.warning(request, f"{missing} item{'s' if missing > 1 else ''} from that order "
                                  f"{'are' if missing > 1 else 'is'} no longer sold.")
    if items:
        messages.success(request, f"Items from order {order.number} are in your cart.")
    return redirect("checkout:cart")
