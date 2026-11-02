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


def _card_page(request, subscription, **context):
    return render(request, "checkout/subscriptions/card.html", {
        "subscription": subscription, "can_update": subscriptions.can_update_card(subscription), **context})


@require_GET
def card(request, token):
    """Pay with a different card: the link in the renewal-failed email (and
    the account page) leads here.  Stripe's Payment Element saves the card
    (a SetupIntent), and Stripe sends the customer on to card_done.  Like
    cancelling, it needs no sign-in, and works while the shop is closed."""
    subscription = get_object_or_404(Subscription, token=token)
    if not subscriptions.can_update_card(subscription):
        return _card_page(request, subscription)
    try:
        started = subscriptions.start_card_update(subscription)
    except payments.PaymentError as exc:
        return _card_page(request, subscription, error=str(exc))
    provider = payments.provider()
    return _card_page(request, subscription, provider=provider.name, publishable_key=provider.publishable_key,
                      client_secret=started.client_secret, intent="setup",
                      return_url=request.build_absolute_uri(reverse("checkout:subscription_card_done", args=[token])),
                      pay_label="Save card" + (" and pay" if subscription.status == Subscription.Status.PAST_DUE else ""),
                      fake_action=reverse("checkout:subscription_card_fake", args=[token]),
                      fake_note="This button stands in for saving a new card.")


def _finish_card(request, subscription, setup_id):
    try:
        result = subscriptions.update_card(subscription, setup_id)
    except payments.PaymentError as exc:
        return _card_page(request, subscription, error=str(exc))
    subscription.refresh_from_db()
    return _card_page(request, subscription, result=result)


@require_GET
def card_done(request, token):
    """Where Stripe sends the customer once the new card is confirmed (or
    refused): ?setup_intent=seti_... names the SetupIntent."""
    subscription = get_object_or_404(Subscription, token=token)
    setup_id = request.GET.get("setup_intent", "")
    if not setup_id.startswith("seti_") or not subscriptions.can_update_card(subscription):
        return redirect("checkout:subscription_card", token=token)
    return _finish_card(request, subscription, setup_id)


@require_POST
def card_fake(request, token):
    """The stand-in for Stripe's card form on a laptop."""
    if payments.provider().name != "fake":
        raise Http404("Not available")
    subscription = get_object_or_404(Subscription, token=token)
    if not subscriptions.can_update_card(subscription):
        return redirect("checkout:subscription_card", token=token)
    return _finish_card(request, subscription, f"fake_seti_{subscription.pk}")


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
