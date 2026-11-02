"""The email list's rules: double opt-in, consent records, frequency caps
and combining, approval, and the headers Gmail and Yahoo require."""

from datetime import date, timedelta

from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.audit import acting_as_agent
from apps.core.testing import make_owner
from apps.emaillist import alerts, sending, services
from apps.emaillist.models import ConsentEvent, Delivery, Mailing, Subscriber

POSTAL = "Teashop LLC\nPO Box 12\nAlbany, NY 12201"
LIST_SETTINGS = dict(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", SHOP_POSTAL_ADDRESS=POSTAL,
                     SITE_URL="https://tea.example", EMAIL_LIST_EMAIL_HOST="", JOBS_EAGER=True,
                     EMAIL_LIST_FROM_EMAIL="Teashop <news@tea.example>")


def subscribed(email="ada@example.com", frequency=Subscriber.Frequency.WEEKLY, confirmed_days_ago=60):
    subscriber = services.request_sign_up(email, frequency, ip="203.0.113.5")
    services.confirm(subscriber)
    Subscriber.objects.filter(pk=subscriber.pk).update(
        confirmed_at=timezone.now() - timedelta(days=confirmed_days_ago))
    subscriber.refresh_from_db()
    return subscriber


def approved(subject="New spring Darjeelings", owner=None, **extra):
    mailing = services.draft_mailing(subject, f"{subject}: details here.", **extra)
    return services.approve(mailing, owner)


@override_settings(**LIST_SETTINGS)
class SignUpTests(TestCase):
    def test_sign_up_waits_for_confirmation(self):
        subscriber = services.request_sign_up(" Ada@Example.COM ", "weekly", ip="203.0.113.5", user_agent="UA")
        self.assertEqual(subscriber.email, "ada@example.com")
        self.assertEqual(subscriber.status, Subscriber.Status.PENDING)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("confirm", message.subject.lower())
        self.assertIn(f"https://tea.example/email-list/confirm/{subscriber.token}/", message.body)
        self.assertIn("PO Box 12", message.body)
        event = subscriber.consent_events.get()
        self.assertEqual((event.action, event.ip_address, event.user_agent, event.frequency),
                         (ConsentEvent.Action.REQUESTED, "203.0.113.5", "UA", "weekly"))
        self.assertIn("unsubscribe", event.wording)
        subscriber.refresh_from_db()
        self.assertIsNotNone(subscriber.confirmation_sent_at)

    def test_confirm_records_consent(self):
        subscriber = services.request_sign_up("ada@example.com", "monthly")
        self.assertEqual(services.confirm(subscriber, ip="198.51.100.1"), "confirmed")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.Status.SUBSCRIBED)
        self.assertEqual(list(subscriber.consent_events.values_list("action", flat=True)),
                         [ConsentEvent.Action.REQUESTED, ConsentEvent.Action.CONFIRMED])
        self.assertEqual(services.confirm(subscriber), "already")

    def test_confirm_link_expires(self):
        subscriber = services.request_sign_up("ada@example.com", "monthly")
        Subscriber.objects.filter(pk=subscriber.pk).update(requested_at=timezone.now() - timedelta(days=8))
        self.assertEqual(services.confirm(subscriber), "expired")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.Status.PENDING)

    def test_signing_up_again_when_subscribed_changes_nothing(self):
        subscriber = subscribed()
        mail.outbox.clear()
        token = subscriber.token
        services.request_sign_up("ada@example.com", "monthly")
        subscriber.refresh_from_db()
        self.assertEqual((subscriber.status, subscriber.frequency, subscriber.token),
                         (Subscriber.Status.SUBSCRIBED, Subscriber.Frequency.WEEKLY, token))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("already", mail.outbox[0].subject)
        self.assertIn(f"/email-list/manage/{token}/", mail.outbox[0].body)

    def test_unsubscribed_must_confirm_again_with_new_links(self):
        subscriber = subscribed()
        old_token = subscriber.token
        services.unsubscribe(subscriber)
        subscriber = services.request_sign_up("ada@example.com", "monthly")
        self.assertEqual(subscriber.status, Subscriber.Status.PENDING)
        self.assertNotEqual(subscriber.token, old_token)

    def test_consent_records_cannot_change(self):
        event = services.request_sign_up("ada@example.com", "monthly").consent_events.get()
        event.wording = "something else"
        with self.assertRaises(ValueError):
            event.save()
        with self.assertRaises(ValueError):
            event.delete()

    def test_unknown_frequency_refused(self):
        with self.assertRaises(ValidationError):
            services.request_sign_up("ada@example.com", "daily")


@override_settings(**LIST_SETTINGS)
class ApprovalTests(TestCase):
    def setUp(self):
        self.owner, _ = make_owner()

    def test_nothing_goes_out_before_approval(self):
        subscribed()
        mail.outbox.clear()
        mailing = services.draft_mailing("Autumn oolongs", "They're here.")
        self.assertEqual(services.dispatch(), 0)
        self.assertEqual(mail.outbox, [])
        services.approve(mailing, self.owner)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Autumn oolongs")

    def test_agents_cannot_approve(self):
        mailing = services.draft_mailing("Autumn oolongs", "They're here.")
        with acting_as_agent("marketing-agent"), self.assertRaises(PermissionDenied):
            services.approve(mailing, self.owner)
        with self.assertRaises(PermissionDenied):
            services.approve(mailing, None)

    @override_settings(SHOP_POSTAL_ADDRESS="")
    def test_needs_postal_address(self):
        mailing = services.draft_mailing("Autumn oolongs", "They're here.")
        with self.assertRaises(ValidationError) as caught:
            services.approve(mailing, self.owner)
        self.assertIn("postal address", " ".join(caught.exception.messages))

    def test_draft_is_an_attention_item_until_approved(self):
        mailing = services.draft_mailing("Autumn oolongs", "They're here.", created_by="marketing-agent")
        items = [i for i in alerts.attention_items() if i.kind == "approvals"]
        self.assertEqual([i.key for i in items], [f"emaillist:mailing:{mailing.pk}"])
        self.assertEqual(items[0].since, mailing.created_at)
        services.approve(mailing, self.owner)
        self.assertFalse([i for i in alerts.attention_items() if i.kind == "approvals"])

    def test_withdrawn_mailing_not_sent_to_those_still_waiting(self):
        subscriber = subscribed()
        approved("First", self.owner)
        mailing = approved("Second", self.owner)  # held back: mailed today
        services.withdraw(mailing)
        mail.outbox.clear()
        self.assertEqual(services.dispatch(today=timezone.localdate() + timedelta(days=7)), 0)
        self.assertEqual(subscriber.deliveries.count(), 1)


@override_settings(**LIST_SETTINGS)
class FrequencyCapTests(TestCase):
    def setUp(self):
        self.owner, _ = make_owner()

    def test_combines_within_the_cap(self):
        weekly = subscribed("weekly@example.com", Subscriber.Frequency.WEEKLY)
        monthly = subscribed("monthly@example.com", Subscriber.Frequency.MONTHLY)
        today = timezone.localdate()
        mail.outbox.clear()  # the confirmation emails
        approved("Spring Darjeeling", self.owner)
        self.assertEqual(len(mail.outbox), 2)  # both were due
        mail.outbox.clear()
        approved("Restocked: Assam", self.owner)
        approved("Tea notes: cold brew", self.owner)
        self.assertEqual(mail.outbox, [])  # nobody due again yet

        self.assertEqual(services.dispatch(today + timedelta(days=6)), 0)
        self.assertEqual(services.dispatch(today + timedelta(days=7)), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["weekly@example.com"])
        self.assertEqual(message.subject, "Tea notes: cold brew, and 1 more update")
        self.assertLess(message.body.index("Tea notes: cold brew"), message.body.index("Restocked: Assam"))
        self.assertNotIn("Spring Darjeeling", message.body)

        mail.outbox.clear()
        self.assertEqual(services.dispatch(today + timedelta(days=30)), 1)
        self.assertEqual(mail.outbox[0].to, ["monthly@example.com"])
        self.assertEqual(set(monthly.deliveries.values_list("mailings__subject", flat=True)),
                         {"Spring Darjeeling", "Restocked: Assam", "Tea notes: cold brew"})
        self.assertEqual(weekly.deliveries.count(), 2)
        # Each mailing reaches each subscriber once.
        self.assertEqual(services.dispatch(today + timedelta(days=60)), 0)

    def test_no_back_issues_for_new_subscribers(self):
        approved("Old news", self.owner)
        subscriber = subscribed(confirmed_days_ago=0)
        self.assertEqual(services.dispatch(), 0)
        self.assertFalse(subscriber.deliveries.exists())

    def test_stale_mailing_dropped_after_send_until(self):
        subscribed()
        today = timezone.localdate()
        approved("Sale starts", self.owner)
        approved("Sale ends Friday", self.owner, send_until=today + timedelta(days=3))
        mail.outbox.clear()
        self.assertEqual(services.dispatch(today + timedelta(days=7)), 0)

    def test_unsubscribed_before_send_is_skipped(self):
        subscriber = subscribed()
        with override_settings(JOBS_EAGER=False):
            approved("Spring Darjeeling", self.owner)
            services.dispatch()
        delivery = Delivery.objects.get()
        services.unsubscribe(subscriber, ConsentEvent.Method.ONE_CLICK)
        mail.outbox.clear()
        sending.send_delivery(delivery.pk)
        delivery.refresh_from_db()
        self.assertIsNotNone(delivery.skipped_at)
        self.assertEqual(mail.outbox, [])

    def test_unsent_delivery_is_flagged(self):
        subscribed()
        with override_settings(JOBS_EAGER=False):
            approved("Spring Darjeeling", self.owner)
            services.dispatch()
        Delivery.objects.update(created_at=timezone.now() - timedelta(hours=1))
        self.assertIn("emaillist:stuck", [i.key for i in alerts.attention_items()])

    def test_due_dates(self):
        subscriber = Subscriber(frequency=Subscriber.Frequency.FORTNIGHTLY, last_mailed_on=date(2026, 3, 1))
        self.assertFalse(subscriber.is_due(date(2026, 3, 14)))
        self.assertTrue(subscriber.is_due(date(2026, 3, 15)))
        self.assertTrue(Subscriber(frequency="monthly").is_due(date(2026, 3, 1)))


@override_settings(**LIST_SETTINGS)
class MessageTests(TestCase):
    def test_bulk_sender_headers_and_footer(self):
        owner, _ = make_owner()
        subscriber = subscribed()
        mail.outbox.clear()
        approved("Spring Darjeeling", owner)
        message = mail.outbox[0]
        unsubscribe = f"https://tea.example/email-list/unsubscribe/{subscriber.token}/"
        self.assertEqual(message.extra_headers["List-Unsubscribe"], f"<{unsubscribe}>")
        self.assertEqual(message.extra_headers["List-Unsubscribe-Post"], "List-Unsubscribe=One-Click")
        self.assertEqual(message.from_email, "Teashop <news@tea.example>")
        self.assertIn(unsubscribe, message.body)
        self.assertIn(f"https://tea.example/email-list/manage/{subscriber.token}/", message.body)
        self.assertIn("PO Box 12", message.body)
        self.assertIn("you signed up", message.body)
        self.assertIsNotNone(Delivery.objects.get().sent_at)

    @override_settings(EMAIL_LIST_EMAIL_HOST="email-smtp.us-east-1.amazonaws.com", EMAIL_LIST_EMAIL_HOST_USER="u",
                       EMAIL_LIST_EMAIL_HOST_PASSWORD="p")
    def test_bulk_sender_connection(self):
        conn = sending.connection()
        self.assertEqual((conn.host, conn.port, conn.username, conn.use_tls),
                         ("email-smtp.us-east-1.amazonaws.com", 587, "u", True))
