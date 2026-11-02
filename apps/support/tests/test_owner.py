"""The owner's side: sending drafts (edited or not), the approval rate and
letting the assistant answer a category alone, and the owner's pages."""

from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.audit import acting_as_agent
from apps.core.testing import login_verified, make_owner
from apps.support import services
from apps.support.models import Category, CategoryMode, Conversation, Draft, Message

from .helpers import SUPPORT_SETTINGS, catalog


def drafted(text="How long does shipping take?", email="ada@example.com"):
    conversation = services.start_chat(email, "Ada", text)
    conversation.refresh_from_db()
    return conversation, conversation.pending_draft()


@override_settings(**SUPPORT_SETTINGS)
class OwnerReplyTests(TestCase):
    def setUp(self):
        catalog()

    def test_draft_sent_unchanged(self):
        conversation, draft = drafted()
        mail.outbox.clear()
        services.owner_reply(conversation, draft.body, draft=draft)
        draft.refresh_from_db()
        self.assertEqual((draft.status, draft.similarity, draft.approved), (Draft.Status.SENT, 1.0, True))
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, Conversation.Status.ANSWERED)
        owner_message = conversation.messages.get(sender=Message.Sender.OWNER)
        self.assertFalse(owner_message.is_ai)
        # A chat reply is emailed too, from the owner: no AI label.
        [sent] = mail.outbox
        self.assertEqual(sent.to, ["ada@example.com"])
        self.assertNotIn("AI assistant", sent.body)
        self.assertIn(conversation.chat_url(), sent.body)

    def test_heavy_edit_is_not_an_approval(self):
        conversation, draft = drafted()
        services.owner_reply(conversation, "Hello!  We pack every order by hand and it usually leaves within a "
                             "couple of days; I'll send tracking as soon as it does.", draft=draft)
        draft.refresh_from_db()
        self.assertFalse(draft.approved)
        self.assertLess(draft.similarity, 0.9)

    def test_small_edit_still_counts(self):
        conversation, draft = drafted()
        services.owner_reply(conversation, draft.body.replace("We weigh", "We always weigh"), draft=draft)
        draft.refresh_from_db()
        self.assertTrue(draft.approved)

    def test_discard_puts_it_back_to_the_owner(self):
        conversation, draft = drafted()
        services.discard_draft(draft)
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, Conversation.Status.ESCALATED)
        self.assertIsNone(conversation.pending_draft())

    def test_draft_used_twice_refused(self):
        conversation, draft = drafted()
        services.owner_reply(conversation, draft.body, draft=draft)
        with self.assertRaises(ValidationError):
            services.owner_reply(conversation, draft.body, draft=draft)


@override_settings(**SUPPORT_SETTINGS)
class ReadinessTests(TestCase):
    def setUp(self):
        catalog()

    def send_drafts(self, count, edit=False):
        for i in range(count):
            conversation, draft = drafted(email=f"c{i}-{edit}@example.com")
            services.owner_reply(conversation, "Something else entirely, written by me." if edit else draft.body,
                                 draft=draft)

    def test_ready_after_enough_approved_drafts(self):
        self.send_drafts(2)
        self.assertFalse(services.readiness(Category.SHIPPING)["ready"])
        with self.assertRaises(ValidationError):
            services.set_answers_alone(Category.SHIPPING, True)
        self.send_drafts(1)
        state = services.readiness(Category.SHIPPING)
        self.assertEqual((state["decided"], state["approved"], state["ready"]), (3, 3, True))
        services.set_answers_alone(Category.SHIPPING, True)
        self.assertTrue(CategoryMode.objects.get(category=Category.SHIPPING).answers_alone)
        services.set_answers_alone(Category.SHIPPING, False)
        self.assertFalse(CategoryMode.objects.get(category=Category.SHIPPING).answers_alone)

    def test_not_ready_when_edited(self):
        self.send_drafts(2)
        self.send_drafts(1, edit=True)
        self.assertFalse(services.readiness(Category.SHIPPING)["ready"])

    def test_never_for_other_and_never_by_an_agent(self):
        with self.assertRaises(ValidationError):
            services.set_answers_alone(Category.OTHER, True)
        self.send_drafts(3)
        with acting_as_agent("support-agent"), self.assertRaises(PermissionDenied):
            services.set_answers_alone(Category.SHIPPING, True)


@override_settings(**SUPPORT_SETTINGS)
class OwnerPageTests(TestCase):
    def setUp(self):
        catalog()
        owner, device = make_owner()
        login_verified(self.client, owner, device)

    def test_inbox_and_sending_a_draft(self):
        conversation, draft = drafted()
        escalated = services.start_chat("bob@example.com", "", "My parcel arrived damaged")
        inbox = self.client.get(reverse("support:owner_inbox"))
        self.assertContains(inbox, "bob@example.com")
        self.assertContains(inbox, "Needs your judgement")
        self.assertContains(inbox, "ada@example.com")
        self.assertContains(inbox, "Watch mode")

        page = self.client.get(conversation.get_absolute_url())
        self.assertContains(page, "edit and send")
        self.assertContains(page, draft.body.split("  ")[0])
        self.assertContains(page, "AI assistant")
        response = self.client.post(conversation.get_absolute_url(), {"body": draft.body, "draft": draft.pk})
        self.assertRedirects(response, reverse("support:owner_inbox"))
        draft.refresh_from_db()
        self.assertTrue(draft.approved)
        self.assertContains(self.client.get(escalated.get_absolute_url()), "Why it came to you")

    def test_discard_and_close(self):
        conversation, draft = drafted()
        self.client.post(reverse("support:owner_discard_draft", args=[conversation.pk]))
        draft.refresh_from_db()
        self.assertEqual(draft.status, Draft.Status.DISCARDED)
        self.client.post(reverse("support:owner_close", args=[conversation.pk]))
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, Conversation.Status.CLOSED)

    def test_category_switch(self):
        url = reverse("support:owner_category", args=["shipping"])
        response = self.client.post(url, {"answers_alone": "1"}, follow=True)
        self.assertContains(response, "Not ready yet")
        self.assertFalse(CategoryMode.objects.filter(answers_alone=True).exists())
        for i in range(3):
            conversation, draft = drafted(email=f"p{i}@example.com")
            services.owner_reply(conversation, draft.body, draft=draft)
        self.assertContains(self.client.get(reverse("support:owner_inbox")), "Let it answer alone")
        self.client.post(url, {"answers_alone": "1"})
        self.assertTrue(CategoryMode.objects.get(category="shipping").answers_alone)
        self.assertEqual(self.client.post(reverse("support:owner_category", args=["nope"])).status_code, 404)

    def test_needs_owner(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("support:owner_inbox")).status_code, 302)
