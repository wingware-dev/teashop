"""Customer accounts without passwords: the customer asks for a sign-in
link, and following the link from their email signs them in.  Nothing to
guess, reuse or leak (NY SHIELD Act), and an account is just an email
address that has proved it is theirs.

A link works once (it names the customer's previous sign-in, which
signing in changes) and for 30 minutes.
"""

from django.core import signing
from django.utils import timezone

from .models import Customer, Order, Subscription

SESSION_KEY = "checkout_customer_id"
SALT = "checkout.sign-in"
MAX_AGE = 30 * 60


def current_customer(request):
    if not hasattr(request, "_checkout_customer"):
        customer_id = request.session.get(SESSION_KEY)
        request._checkout_customer = Customer.objects.filter(pk=customer_id).first() if customer_id else None
    return request._checkout_customer


def _stamp(customer):
    return customer.last_sign_in_at.isoformat() if customer and customer.last_sign_in_at else ""


def sign_in_token(email):
    email = email.strip().lower()
    return signing.dumps({"e": email, "s": _stamp(Customer.objects.filter(email=email).first())}, salt=SALT)


def redeem(token):
    """The customer the token signs in (made on first sign-in), or None if
    it is bad, expired or used."""
    try:
        data = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except signing.BadSignature:  # includes SignatureExpired
        return None
    email = data.get("e", "")
    customer = Customer.objects.filter(email=email).first()
    if data.get("s", "") != _stamp(customer):
        return None
    if customer is None:
        customer = Customer.objects.create(email=email)
    customer.last_sign_in_at = timezone.now()
    customer.save(update_fields=["last_sign_in_at"])
    # Orders and subscriptions placed as a guest with this email are theirs.
    Order.objects.filter(email__iexact=email, customer=None).update(customer=customer)
    Subscription.objects.filter(email__iexact=email, customer=None).update(customer=customer)
    return customer


def sign_in(request, customer):
    from .cart import get_cart

    request.session.cycle_key()
    request.session[SESSION_KEY] = customer.pk
    request._checkout_customer = customer
    cart = get_cart(request)
    if cart and cart.customer_id is None:
        cart.customer = customer
        cart.save(update_fields=["customer"])


def sign_out(request):
    request.session.pop(SESSION_KEY, None)
    request._checkout_customer = None
