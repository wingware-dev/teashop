"""The email list's pages: sign-up, confirmation, one-click unsubscribe,
changing frequency, and the owner's approval pages."""

import time

from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.checkout import protection
from apps.core.testing import login_verified, make_owner
from apps.emaillist import services
from apps.emaillist.models import ConsentEvent, Mailing, Subscriber

from .test_services import LIST_SETTINGS, subscribed

VIEW_SETTINGS = dict(
    LIST_SETTINGS, STOREFRONT_OPEN=True, TURNSTILE_SITE_KEY="", TURNSTILE_SECRET_KEY="", CHECKOUT_MIN_FORM_SECONDS=0,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "emaillist-tests"}})


def form_data(**extra):
    return {protection.STAMP_FIELD: protection.form_stamp(time.time() - 60), **extra}


@override_settings(**VIEW_SETTINGS)
class PublicPageTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_sign_up_form_and_confirmation(self):
        page = self.client.get(reverse("emaillist:sign_up"))
        self.assertContains(page, "How often, at most")
        self.assertRegex(page.content.decode(), r'value="monthly"[^>]* checked')
        response = self.client.post(reverse("emaillist:sign_up"),
                                    form_data(email="Ada@Example.com", frequency="fortnightly"),
                                    HTTP_USER_AGENT="Firefox")
        self.assertContains(response, "Check your email")
        subscriber = Subscriber.objects.get()
        self.assertEqual((subscriber.status, subscriber.frequency), ("pending", "fortnightly"))
        self.assertEqual(subscriber.consent_events.get().user_agent, "Firefox")

        confirm = reverse("emaillist:confirm", args=[subscriber.token])
        self.assertContains(self.client.get(confirm), "Yes, sign me up")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, "pending")  # opening the link alone does nothing
        self.assertContains(self.client.post(confirm), "You're on the list")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, "subscribed")

    def test_honeypot_refused(self):
        response = self.client.post(reverse("emaillist:sign_up"),
                                    form_data(email="bot@example.com", frequency="weekly", website="spam"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Subscriber.objects.exists())

    def test_confirmation_emails_limited_per_address(self):
        for _ in range(5):
            self.client.post(reverse("emaillist:sign_up"), form_data(email="ada@example.com", frequency="weekly"))
        # Three tries an hour per address, each with a fresh link (the
        # earlier links stop working).
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(ConsentEvent.objects.count(), 3)
        self.assertIn(Subscriber.objects.get().token, mail.outbox[-1].body)

    @override_settings(STOREFRONT_OPEN=False)
    def test_sign_up_hidden_until_shop_opens(self):
        self.assertEqual(self.client.get(reverse("emaillist:sign_up")).status_code, 404)

    def test_one_click_unsubscribe(self):
        subscriber = subscribed()
        # As a mail app sends it (RFC 8058): no cookies, no CSRF token.
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("emaillist:unsubscribe", args=[subscriber.token]),
                               {"List-Unsubscribe": "One-Click"})
        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, "unsubscribed")
        self.assertEqual(subscriber.consent_events.last().method, ConsentEvent.Method.ONE_CLICK)

    @override_settings(STOREFRONT_OPEN=False)
    def test_unsubscribe_link_asks_then_works_even_when_shop_closed(self):
        subscriber = subscribed()
        url = reverse("emaillist:unsubscribe", args=[subscriber.token])
        self.assertContains(self.client.get(url), "Unsubscribe")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, "subscribed")
        self.assertContains(self.client.post(url), "You're unsubscribed")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, "unsubscribed")
        self.assertEqual(subscriber.consent_events.last().method, ConsentEvent.Method.LINK)

    def test_change_frequency(self):
        subscriber = subscribed(frequency="weekly")
        url = reverse("emaillist:manage", args=[subscriber.token])
        self.assertRegex(self.client.get(url).content.decode(), r'value="weekly"[^>]* checked')
        self.client.post(url, {"frequency": "monthly"})
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.frequency, "monthly")
        self.assertEqual(subscriber.consent_events.last().action, ConsentEvent.Action.FREQUENCY)

    def test_unknown_token(self):
        for name in ("confirm", "manage", "unsubscribe"):
            self.assertEqual(self.client.get(reverse(f"emaillist:{name}", args=["nope"])).status_code, 404)


@override_settings(**VIEW_SETTINGS)
class OwnerPageTests(TestCase):
    def setUp(self):
        user, device = make_owner()
        login_verified(self.client, user, device)

    def test_write_preview_approve(self):
        subscribed()
        mail.outbox.clear()
        response = self.client.post(reverse("emaillist:mailing_new"),
                                    {"subject": "Autumn oolongs", "body": "Roasted and ready.", "send_until": ""})
        mailing = Mailing.objects.get()
        self.assertRedirects(response, reverse("emaillist:mailing", args=[mailing.pk]))
        page = self.client.get(reverse("emaillist:mailing", args=[mailing.pk]))
        self.assertContains(page, "Roasted and ready.")
        self.assertContains(page, "PO Box 12")
        self.assertContains(page, "Approve and send")
        self.assertEqual(mail.outbox, [])
        self.client.post(reverse("emaillist:mailing_approve", args=[mailing.pk]))
        mailing.refresh_from_db()
        self.assertEqual(mailing.status, Mailing.Status.APPROVED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(self.client.get(reverse("emaillist:owner_home")), "Autumn oolongs")

    def test_customers_cannot_reach_owner_pages(self):
        self.assertEqual(Client().get(reverse("emaillist:owner_home")).status_code, 302)
        mailing = services.draft_mailing("x", "y")
        response = Client().post(reverse("emaillist:mailing_approve", args=[mailing.pk]))
        self.assertEqual(response.status_code, 302)
        mailing.refresh_from_db()
        self.assertEqual(mailing.status, Mailing.Status.DRAFT)
