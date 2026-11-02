"""The email list's pages: signing up, confirming, changing how often or
unsubscribing (from links in the emails), and the owner's mailings."""

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from apps.checkout import protection
from apps.checkout.views import shop_view
from apps.core.decorators import owner_required
from apps.core.net import client_ip

from . import sending, services
from .forms import FrequencyForm, MailingForm, SignUpForm
from .models import ConsentEvent, Mailing, Subscriber


def _who(request):
    return {"ip": client_ip(request), "user_agent": request.META.get("HTTP_USER_AGENT", "")}


# -- Public pages ----------------------------------------------------------------

@shop_view
@require_http_methods(["GET", "POST"])
def sign_up(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        refused = protection.check(request, "email-list", settings.EMAIL_LIST_RATE_LIMIT)
        if refused:
            messages.error(request, refused)
        elif form.is_valid():
            email = services.normalize(form.cleaned_data["email"])
            # A few tries per address an hour, so the form can't be used to
            # flood someone with confirmation emails.
            if not protection.over_limit(request, f"email-list-email:{email}", 3):
                services.request_sign_up(email, form.cleaned_data["frequency"], wording=services.sign_up_wording(),
                                         **_who(request))
            # The same answer whoever it is, so the page can't tell anyone
            # who is on the list.
            return render(request, "emaillist/check_email.html", {"email": email})
    else:
        form = SignUpForm()
    return render(request, "emaillist/sign_up.html", {"form": form, "wording": services.sign_up_wording(),
                                                      **protection.context()})


def _bad_link(request):
    return render(request, "emaillist/bad_link.html", status=404)


@never_cache
@require_http_methods(["GET", "POST"])
def confirm(request, token):
    """GET shows a button; only the POST confirms, so mail scanners that
    open links don't sign anyone up."""
    subscriber = services.by_token(token)
    if subscriber is None:
        return _bad_link(request)
    if request.method == "POST":
        outcome = services.confirm(subscriber, **_who(request))
        if outcome == "expired":
            return render(request, "emaillist/confirm.html", {"subscriber": subscriber, "expired": True})
        subscriber.refresh_from_db()
        return render(request, "emaillist/confirmed.html", {"subscriber": subscriber})
    if subscriber.status == Subscriber.Status.SUBSCRIBED:
        return redirect("emaillist:manage", token)
    expired = subscriber.status != Subscriber.Status.PENDING or subscriber.confirm_expired()
    return render(request, "emaillist/confirm.html", {"subscriber": subscriber, "expired": expired})


@never_cache
@require_http_methods(["GET", "POST"])
def manage(request, token):
    """Change how often, or unsubscribe: the link at the foot of each email."""
    subscriber = services.by_token(token)
    if subscriber is None:
        return _bad_link(request)
    if request.method == "POST" and subscriber.status == Subscriber.Status.SUBSCRIBED:
        form = FrequencyForm(request.POST)
        if form.is_valid():
            services.set_frequency(subscriber, form.cleaned_data["frequency"], **_who(request))
            messages.success(request, "Saved.  " + Subscriber.Frequency(form.cleaned_data["frequency"]).label + ".")
            return redirect("emaillist:manage", token)
    else:
        form = FrequencyForm(initial={"frequency": subscriber.frequency})
    return render(request, "emaillist/manage.html", {"subscriber": subscriber, "form": form})


@csrf_exempt
@never_cache
@require_http_methods(["GET", "POST"])
def unsubscribe(request, token):
    """GET asks to confirm with one button (mail scanners open links); a
    POST unsubscribes at once.  Mail apps' own Unsubscribe buttons POST
    here with List-Unsubscribe=One-Click (RFC 8058), with no cookies or
    CSRF token, so this view is CSRF-exempt: the secret token in the
    address is the proof, and the worst a forged POST can do is the
    unsubscribe the link exists for."""
    subscriber = services.by_token(token)
    if subscriber is None:
        return _bad_link(request)
    if request.method == "POST":
        one_click = request.POST.get("List-Unsubscribe") == "One-Click"
        method = ConsentEvent.Method.ONE_CLICK if one_click else ConsentEvent.Method.LINK
        services.unsubscribe(subscriber, method, **_who(request))
        subscriber.refresh_from_db()
        return render(request, "emaillist/unsubscribed.html", {"subscriber": subscriber})
    if subscriber.status == Subscriber.Status.UNSUBSCRIBED:
        return render(request, "emaillist/unsubscribed.html", {"subscriber": subscriber})
    return render(request, "emaillist/unsubscribe.html", {"subscriber": subscriber})


# -- The owner's pages -------------------------------------------------------------

@never_cache
@owner_required
def owner_home(request):
    today = timezone.localdate()
    subscribed = Subscriber.objects.filter(status=Subscriber.Status.SUBSCRIBED)
    by_frequency = [(label, subscribed.filter(frequency=value).count())
                    for value, label in Subscriber.Frequency.choices]
    month_ago = timezone.now() - timedelta(days=30)
    drafts = list(Mailing.objects.filter(status=Mailing.Status.DRAFT).order_by("created_at"))
    approved = [(m, *services.reach(m, today)) for m in
                Mailing.objects.filter(status=Mailing.Status.APPROVED).order_by("-approved_at")[:20]]
    return render(request, "emaillist/owner/home.html", {
        "subscribed": subscribed.count(), "by_frequency": by_frequency,
        "pending": Subscriber.objects.filter(status=Subscriber.Status.PENDING,
                                             requested_at__gte=timezone.now() - settings.EMAIL_LIST_CONFIRM_WITHIN)
        .count(),
        "joined_30": subscribed.filter(confirmed_at__gte=month_ago).count(),
        "left_30": Subscriber.objects.filter(status=Subscriber.Status.UNSUBSCRIBED,
                                             unsubscribed_at__gte=month_ago).count(),
        "drafts": drafts, "approved": approved,
        "postal_address": settings.SHOP_POSTAL_ADDRESS.strip(),
        "sign_up_url": request.build_absolute_uri(reverse("emaillist:sign_up")),
    })


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def mailing_edit(request, pk=None):
    mailing = get_object_or_404(Mailing, pk=pk) if pk else None
    if mailing is not None and mailing.status != Mailing.Status.DRAFT:
        messages.info(request, "Only drafts can be changed.  Withdraw it and write a new one instead.")
        return redirect("emaillist:mailing", mailing.pk)
    if request.method == "POST":
        form = MailingForm(request.POST, instance=mailing)
        if form.is_valid():
            if mailing is None:
                data = form.cleaned_data
                mailing = services.draft_mailing(data["subject"], data["body"], data["send_until"],
                                                 created_by=request.user.get_username())
            else:
                mailing = form.save()
            return redirect("emaillist:mailing", mailing.pk)
    else:
        form = MailingForm(instance=mailing)
    return render(request, "emaillist/owner/mailing_form.html", {"form": form, "mailing": mailing})


class _Preview:
    """A stand-in subscriber for the preview: the links in it go nowhere."""

    email = "subscriber@example.com"
    token = "preview"

    def get_frequency_display(self):
        return Subscriber.Frequency.MONTHLY.label

    def manage_url(self):
        return "/email-list/manage/preview/"

    def unsubscribe_url(self):
        return "/email-list/unsubscribe/preview/"


@never_cache
@owner_required
def mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    today = timezone.localdate()
    sent, waiting = services.reach(mailing, today)
    return render(request, "emaillist/owner/mailing.html", {
        "mailing": mailing, "preview": sending.render_mailing(_Preview(), [mailing]),
        "problems": services.approval_problems(mailing, today) if mailing.status == Mailing.Status.DRAFT else [],
        "sent": sent, "waiting": waiting,
        "subscribed": Subscriber.objects.filter(status=Subscriber.Status.SUBSCRIBED).count(),
    })


@owner_required
@require_POST
def mailing_approve(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    try:
        services.approve(mailing, request.user)
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
    else:
        messages.success(request, "Approved.  It goes now to subscribers who are due an email, and to the others "
                                  "as soon as their chosen frequency allows.")
    return redirect("emaillist:mailing", pk)


@owner_required
@require_POST
def mailing_withdraw(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    was_draft = mailing.status == Mailing.Status.DRAFT
    services.withdraw(mailing)
    messages.success(request, "Draft discarded." if was_draft else "Withdrawn: it goes to nobody else.")
    return redirect("emaillist:owner_home")
