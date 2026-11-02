"""Support pages in a real browser: phone and desktop, light and dark, WCAG
2.2 AA checks, screenshots (see apps.core.uitesting).  The flow test starts
a chat as a customer does and sees the AI-labelled answer arrive, then the
owner edits and sends the draft."""

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from apps.core.uitesting import BrowserTestCase
from apps.support import services
from apps.support.models import Conversation, Draft

from .helpers import SUPPORT_SETTINGS, catalog, order

UI_SETTINGS = dict(SUPPORT_SETTINGS, CHECKOUT_MIN_FORM_SECONDS=0)


@override_settings(**UI_SETTINGS)
class SupportUITests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        catalog()

    def drafted(self):
        placed = order()
        conversation = services.start_chat("ada@example.com", "Ada", f"Hello, where is my order {placed.number}?")
        services.start_chat("bob@example.com", "", "My tin arrived dented, can I get a replacement?")
        return conversation

    def test_chat_start(self):
        self.check_page(reverse("support:chat_start"), "support-chat-start")

    def test_chat(self):
        self.check_page(self.drafted().chat_url(), "support-chat")

    def test_owner_inbox(self):
        self.drafted()
        self.check_page(reverse("support:owner_inbox"), "support-owner-inbox", signed_in=True)

    def test_owner_conversation(self):
        self.check_page(self.drafted().get_absolute_url(), "support-owner-conversation", signed_in=True)

    def test_agents_page(self):
        self.drafted()
        self.check_page(reverse("agents:owner_home"), "agents-owner-home", signed_in=True)

    def test_chat_flow(self):
        page = self.new_page("phone", "light")
        page.goto(self.url(reverse("support:chat_start")))
        page.get_by_label("Your email").fill("grace@example.com")
        page.get_by_label("Your question").fill("How should I brew the Sencha Morning Mist?")
        page.get_by_role("button", name="Start the chat").click()
        page.get_by_text("A person at the shop checks my answers").wait_for()
        self.assertEqual(page.locator(".ai-badge").count(), 1)
        self.check_current(page, "support-flow-chat-waiting")

        conversation = Conversation.objects.get(email="grace@example.com")
        draft = conversation.pending_draft()
        self.assertIn("75 °C", draft.body)

        owner = self.new_page("desktop", "light", signed_in=True)
        owner.goto(self.url(conversation.get_absolute_url()))
        box = owner.get_by_label("Reply")
        self.assertIn("75 °C", box.input_value())
        box.fill("Hi Grace!  " + draft.body)
        self.check_current(owner, "support-flow-owner-edits")
        owner.get_by_role("button", name="Send (in the chat and by email)").click()
        owner.get_by_role("heading", name="Customer support").wait_for()
        self.check_current(owner, "support-flow-owner-sent")
        draft.refresh_from_db()
        self.assertEqual(draft.status, Draft.Status.SENT)

        page.reload()
        page.get_by_text("Hi Grace!").wait_for()
        self.check_current(page, "support-flow-chat-answered")
