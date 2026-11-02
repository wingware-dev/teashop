"""The email list's pages in a real browser: phone and desktop, light and
dark, WCAG 2.2 AA checks, screenshots (see apps.core.uitesting).  The flow
test signs up through the form, confirms, changes frequency and
unsubscribes, as a customer does."""

from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from apps.core.uitesting import BrowserTestCase
from apps.emaillist import services
from apps.emaillist.models import Subscriber

from .test_views import VIEW_SETTINGS


def subscriber(status="subscribed"):
    person = services.request_sign_up("ada@example.com", "fortnightly")
    if status != "pending":
        services.confirm(person)
    if status == "unsubscribed":
        services.unsubscribe(person)
    person.refresh_from_db()
    return person


@override_settings(**VIEW_SETTINGS)
class EmailListUITests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def test_sign_up(self):
        self.check_page(reverse("emaillist:sign_up"), "emaillist-sign-up")

    def test_confirm(self):
        self.check_page(reverse("emaillist:confirm", args=[subscriber("pending").token]), "emaillist-confirm")

    def test_manage(self):
        self.check_page(reverse("emaillist:manage", args=[subscriber().token]), "emaillist-manage")

    def test_unsubscribe(self):
        self.check_page(reverse("emaillist:unsubscribe", args=[subscriber().token]), "emaillist-unsubscribe")

    def test_unsubscribed(self):
        self.check_page(reverse("emaillist:unsubscribe", args=[subscriber("unsubscribed").token]),
                        "emaillist-unsubscribed")

    def test_sign_up_flow(self):
        page = self.new_page("phone", "light")
        page.goto(self.url(reverse("emaillist:sign_up")))
        page.get_by_label("Email").fill("grace@example.com")
        page.get_by_label("At most once every two weeks").check()
        page.get_by_role("button", name="Sign me up").click()
        page.get_by_role("heading", name="Check your email").wait_for()
        self.check_current(page, "emaillist-flow-check-email")

        person = Subscriber.objects.get(email="grace@example.com")
        self.assertIn(person.token, mail.outbox[-1].body)
        page.goto(self.url(reverse("emaillist:confirm", args=[person.token])))
        page.get_by_role("button", name="Yes, sign me up").click()
        page.get_by_role("heading", name="You're on the list").wait_for()
        self.check_current(page, "emaillist-flow-confirmed")

        page.get_by_role("link", name="change it now").click()
        page.get_by_label("At most once a month").check()
        page.get_by_role("button", name="Save").click()
        page.get_by_text("Saved.").wait_for()
        self.check_current(page, "emaillist-flow-frequency-saved")
        page.get_by_role("button", name="Unsubscribe").click()
        page.get_by_role("heading", name="You're unsubscribed").wait_for()
        self.check_current(page, "emaillist-flow-unsubscribed")
        person.refresh_from_db()
        self.assertEqual((person.status, person.frequency), ("unsubscribed", "monthly"))
        self.assertEqual(person.consent_events.count(), 4)

    def test_owner_home(self):
        owner = self.owner()[0]
        subscriber()
        services.draft_mailing("Autumn oolongs are in", "Three roasted oolongs from Taiwan.", created_by="owner")
        sent = services.draft_mailing("Spring Darjeeling, first flush", "Bright and floral.\n\nOrder by Friday.")
        services.approve(sent, owner)
        self.check_page(reverse("emaillist:owner_home"), "emaillist-owner-home", signed_in=True)

    def test_owner_mailing_draft(self):
        subscriber()
        mailing = services.draft_mailing(
            "Autumn oolongs are in", "Three roasted oolongs from Taiwan, each picked by hand.\n\n"
            "Read more at https://tea.example/teas/oolong/ and order by Friday for the first batch.",
            created_by="marketing-agent")
        self.check_page(reverse("emaillist:mailing", args=[mailing.pk]), "emaillist-owner-mailing", signed_in=True)

    def test_owner_mailing_form(self):
        self.check_page(reverse("emaillist:mailing_new"), "emaillist-owner-mailing-form", signed_in=True)
