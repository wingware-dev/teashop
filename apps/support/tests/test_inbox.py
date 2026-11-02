"""The support inbox: which emails reach the assistant, threading, quoted
text, and reading the mailbox over IMAP (mocked)."""

from unittest import mock

from django.test import TestCase, override_settings

from apps.audit.models import AuditEvent
from apps.support import inbox, services
from apps.support.models import Conversation, Message

from .helpers import SUPPORT_SETTINGS, catalog, raw_email


@override_settings(**SUPPORT_SETTINGS)
class ReceiveTests(TestCase):
    def setUp(self):
        catalog()

    def test_new_email_starts_a_conversation(self):
        message = inbox.receive(raw_email("How long does shipping take?", subject="Shipping question"))
        conversation = message.conversation
        self.assertEqual((conversation.channel, conversation.email, conversation.name, conversation.subject),
                         ("email", "ada@example.com", "Ada", "Shipping question"))
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, Conversation.Status.DRAFTED)
        self.assertTrue(AuditEvent.objects.filter(action="support.message_received").exists())

    def test_automatic_mail_is_skipped(self):
        for headers in [{"Auto-Submitted": "auto-replied"}, {"Precedence": "bulk"}, {"List-Id": "<news.x>"},
                        {"X-Autoreply": "yes"}]:
            with self.subTest(headers=headers):
                self.assertIsNone(inbox.receive(raw_email(headers=headers)))
        self.assertIsNone(inbox.receive(raw_email(sender="MAILER-DAEMON@mail.example")))
        self.assertIsNone(inbox.receive(raw_email(sender="Teashop <help@teashop.example>")))
        self.assertFalse(Message.objects.exists())

    def test_same_email_twice_is_kept_once(self):
        raw = raw_email("Shipping to Ohio?")
        inbox.receive(raw)
        self.assertIsNone(inbox.receive(raw))
        self.assertEqual(Message.objects.filter(sender="customer").count(), 1)

    def test_reply_threads_and_quotes_are_dropped(self):
        first = inbox.receive(raw_email("My parcel is damaged", subject="Damaged tin"))
        conversation = first.conversation
        ours = conversation.messages.get(sender=Message.Sender.AGENT)  # the hold notice, emailed
        self.assertTrue(ours.email_message_id)
        reply = raw_email("Here is a photo.\n\nOn Mon, Nov 2, 2026 at 9:00 Teashop wrote:\n> Thanks for writing",
                          subject="Re: Something else", headers={"In-Reply-To": ours.email_message_id})
        message = inbox.receive(reply)
        self.assertEqual(message.conversation, conversation)
        self.assertEqual(message.body, "Here is a photo.")

    def test_same_sender_and_subject_threads(self):
        first = inbox.receive(raw_email("Shipping time?", subject="Question"))
        second = inbox.receive(raw_email("Also, to Maine?", subject="RE: Question"))
        self.assertEqual(first.conversation, second.conversation)
        other = inbox.receive(raw_email("Brewing?", subject="Another thing"))
        self.assertNotEqual(other.conversation, first.conversation)

    def test_html_only_email(self):
        message = inbox.receive(raw_email(html="<p>How long does <b>shipping</b> take?</p><p>Thanks</p>"))
        self.assertIn("How long does shipping take?", message.body)
        self.assertNotIn("<", message.body)

    def test_reply_to_a_closed_conversation_reopens_it(self):
        first = inbox.receive(raw_email("Shipping time?", subject="Question"))
        services.close(first.conversation)
        inbox.receive(raw_email("One more thing about shipping times", subject="Re: Question"))
        first.conversation.refresh_from_db()
        self.assertNotEqual(first.conversation.status, Conversation.Status.CLOSED)


class FakeImap:
    def __init__(self, emails):
        self.emails, self.seen, self.logged_in = emails, [], None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def login(self, user, password):
        self.logged_in = user

    def select(self, folder):
        return "OK", [b"1"]

    def uid(self, command, *args):
        if command == "search":
            return "OK", [b" ".join(self.emails)]
        if command == "fetch":
            return "OK", [(b"1 (BODY[] {100}", self.emails[args[0]]), b")"]
        if command == "store":
            self.seen.append(args[0])
            return "OK", []
        raise AssertionError(command)


@override_settings(**dict(SUPPORT_SETTINGS, SUPPORT_INBOX="imap", SUPPORT_IMAP_HOST="imap.example",
                          SUPPORT_IMAP_USER="help", SUPPORT_IMAP_PASSWORD="pw"))
class PollTests(TestCase):
    def setUp(self):
        catalog()

    def test_poll_reads_and_marks_seen(self):
        emails = {b"7": raw_email("Shipping time?"), b"8": raw_email("Broken", subject="Bad")}
        imap = FakeImap(emails)
        with mock.patch("apps.support.inbox.imaplib.IMAP4_SSL", return_value=imap):
            self.assertEqual(inbox.poll(), 2)
        self.assertEqual(imap.seen, [b"7", b"8"])
        self.assertEqual(imap.logged_in, "help")
        self.assertEqual(Conversation.objects.count(), 2)

    def test_an_unreadable_email_does_not_stop_the_rest(self):
        emails = {b"1": raw_email("first"), b"2": raw_email("Shipping time?", subject="Two")}
        imap = FakeImap(emails)
        real = inbox.receive

        def flaky(raw):
            if b"first" in raw:
                raise ValueError("bad email")
            return real(raw)

        with mock.patch("apps.support.inbox.imaplib.IMAP4_SSL", return_value=imap), \
                mock.patch("apps.support.inbox.receive", side_effect=flaky), \
                self.assertLogs("apps.support.inbox", "ERROR"):
            inbox.poll()
        self.assertEqual(imap.seen, [b"1", b"2"])
        self.assertTrue(AuditEvent.objects.filter(action="support.email_unreadable").exists())
        self.assertEqual(Conversation.objects.count(), 1)
