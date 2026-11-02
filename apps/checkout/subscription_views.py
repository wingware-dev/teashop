"""Signing up for a tea subscription, paying for it, and cancelling it in
one step (see subscriptions.py for the law these follow)."""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import payments, protection, shipping, subscriptions
from .accounts import current_customer
from .forms import SubscribeForm
from .models import Subscription, SubscriptionPlan
from .views import checkout_open, shop_view

SECRET_KEY = "checkout_subscription_secret"


@shop_view
@require_GET
def plans(request):
    return render(request, "checkout/subscriptions/plans.html",
                  {"plans": SubscriptionPlan.objects.filter(is_active=True), "closed": checkout_open()})


@shop_view
@require_http_methods(["GET", "POST"])
def subscribe(request, slug):
    plan = get_object_or_404(SubscriptionPlan, slug=slug, is_active=True)
    closed = checkout_open()
    customer = current_customer(request)
    if request.method == "POST" and not closed:
        form = SubscribeForm(request.POST)
        refused = protection.check(request, "subscribe")
        if refused:
            messages.error(request, refused)
        elif form.is_valid():
            try:
                checked = shipping.provider().verify(form.address())
            except shipping.ShippingError as exc:
                messages.error(request, str(exc))
            else:
                if not checked.ok:
                    for message in checked.messages:
                        form.add_error(None, message)
                else:
                    try:
                        subscription, started = subscriptions.start(plan, form.cleaned_data["email"],
                                                                    checked.address, customer)
                    except payments.PaymentError as exc:
                        messages.error(request, str(exc))
                    else:
                        request.session[SECRET_KEY] = {subscription.token: started.client_secret}
                        return redirect("checkout:subscription_pay", token=subscription.token)
    else:
        initial = SubscribeForm.initial_from(customer.email if customer else "",
                                             customer.address if customer and customer.has_address else None)
        form = SubscribeForm(initial=initial)
    return render(request, "checkout/subscriptions/subscribe.html",
                  {"plan": plan, "form": form, "closed": closed, **protection.context()})


def _pending(request, token):
    subscription = get_object_or_404(Subscription, token=token)
    if subscription.status != Subscription.Status.PENDING:
        return subscription, None
    secret = (request.session.get(SECRET_KEY) or {}).get(token)
    if secret is None:
        # Only the browser that signed up may pay for it.
        raise Http404("No such sign-up in progress")
    return subscription, secret


@shop_view
@require_GET
def pay(request, token):
    subscription, secret = _pending(request, token)
    if secret is None:
        return redirect("checkout:subscription_welcome", token=token)
    provider = payments.provider()
    return render(request, "checkout/subscriptions/pay.html", {
        "subscription": subscription, "provider": provider.name, "publishable_key": provider.publishable_key,
        "client_secret": secret,
        "return_url": request.build_absolute_uri(reverse("checkout:subscription_welcome", args=[token])),
        "pay_label": f"Subscribe and pay ${subscription.price:,.2f}",
        "fake_action": reverse("checkout:subscription_fake_pay", args=[token]),
    })


@shop_view
@require_POST
def fake_pay(request, token):
    if payments.provider().name != "fake":
        raise Http404("Not available")
    subscription, secret = _pending(request, token)
    if secret is not None:
        subscriptions.record_payment(subscription, first=True, invoice_id=f"fake_in_{subscription.pk}_1")
    return redirect("checkout:subscription_welcome", token=token)


@require_GET
def welcome(request, token):
    subscription = get_object_or_404(Subscription, token=token)
    (request.session.get(SECRET_KEY) or {}).pop(token, None)
    request.session.modified = True
    return render(request, "checkout/subscriptions/welcome.html", {"subscription": subscription})


@require_http_methods(["GET", "POST"])
def cancel(request, token):
    """One-step online cancellation: the link in every subscription email
    (and the account page) leads here, and one button cancels.  No sign-in,
    no questions, no offers in the way."""
    subscription = get_object_or_404(Subscription, token=token)
    if request.method == "POST":
        try:
            subscriptions.cancel(subscription)
        except payments.PaymentError as exc:
            messages.error(request, str(exc))
        return redirect("checkout:subscription_cancel", token=token)
    return render(request, "checkout/subscriptions/cancel.html", {"subscription": subscription})
