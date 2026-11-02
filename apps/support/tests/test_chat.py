"""The customer's chat pages: starting a chat, the conversation, the JSON
the page polls, the AI labelling and the bot protection."""

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.support.models import Conversation, Message

from .helpers import SUPPORT_SETTINGS, catalog, form_data


@override_settings(**SUPPORT_SETTINGS)
class ChatTests(TestCase):
    def setUp(self):
        cache.clear()
        catalog()

    def start(self, message="How long does shipping take?"):
        return self.client.post(reverse("support:chat_start"),
                                form_data(email="Ada@Example.com", name="Ada", message=message))

    def test_start_page_says_it_is_an_ai(self):
        page = self.client.get(reverse("support:chat_start"))
        self.assertContains(page, "AI assistant")
        self.assertContains(page, "an AI")

    def test_chat_flow(self):
        response = self.start()
        conversation = Conversation.objects.get()
        self.assertRedirects(response, conversation.chat_url() + "#latest", fetch_redirect_response=False)
        self.assertEqual(conversation.email, "ada@example.com")
        page = self.client.get(conversation.chat_url())
        self.assertContains(page, "How long does shipping take?")
        self.assertContains(page, '<span class="ai-badge">AI assistant</span>', html=True)
        self.assertContains(page, "A person at the shop will reply here")

        self.client.post(conversation.chat_url(), form_data(message="And to Maine?"))
        self.assertEqual(conversation.messages.filter(sender=Message.Sender.CUSTOMER).count(), 2)

    def test_messages_json(self):
        self.start()
        conversation = Conversation.objects.get()
        first = conversation.messages.first()
        data = self.client.get(reverse("support:chat_messages", args=[conversation.token]),
                               {"after": first.pk}).json()
        self.assertEqual([m["sender"] for m in data["messages"]], ["agent"])
        self.assertTrue(data["messages"][0]["ai"])
        self.assertFalse(data["waiting"])

    def test_unknown_chat(self):
        self.assertEqual(self.client.get(reverse("support:chat", args=["nope"])).status_code, 404)

    def test_honeypot_refused(self):
        self.client.post(reverse("support:chat_start"),
                         form_data(email="bot@example.com", message="buy now", website="spam"))
        self.assertFalse(Conversation.objects.exists())

    @override_settings(SUPPORT_CHAT_RATE_LIMIT=2)
    def test_rate_limit(self):
        for _ in range(3):
            self.start()
        self.assertEqual(Conversation.objects.count(), 2)

    @override_settings(STOREFRONT_OPEN=False)
    def test_closed_until_the_shop_opens(self):
        self.assertEqual(self.client.get(reverse("support:chat_start")).status_code, 404)

    def test_footer_links_to_the_chat(self):
        self.assertContains(self.client.get(reverse("storefront:home")), reverse("support:chat_start"))
