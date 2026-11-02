"""The marketing guardrails: what blocks a post's approval, and what the
owner is only warned about."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.checkout.models import DiscountCode
from apps.marketing import guardrails
from apps.marketing.models import Campaign, Post

from .helpers import MARKETING_SETTINGS, catalog, tomorrow


@override_settings(**MARKETING_SETTINGS)
class GuardrailTests(TestCase):
    def setUp(self):
        self.assam = catalog()

    def post(self, text, network="bluesky", **fields):
        fields.setdefault("scheduled_for", tomorrow())
        return Post(network=network, text=text, **fields)

    def test_plain_post_passes(self):
        post = self.post("Assam Second Flush: malty, brisk and good with milk.", link="/products/assam-second-flush/",
                         product=self.assam)
        self.assertEqual(guardrails.problems(post), [])
        self.assertIn("utm_source=bluesky", post.final_text())

    def test_health_claims_block_everyone(self):
        for made_by in ("owner", "marketing-agent"):
            with self.subTest(made_by=made_by):
                problems = guardrails.problems(self.post("Our green tea boosts immunity and helps you detox.",
                                                         made_by=made_by))
                self.assertTrue(any("health or disease claim" in p.lower() for p in problems), problems)

    def test_testimonials_block_the_agent_and_warn_the_owner(self):
        text = "\"Best cup I've had all year\" - Margaret.  Customers love it: ★★★★★"
        agent_post = self.post(text, made_by="marketing-agent")
        self.assertTrue(any("testimonial" in p for p in guardrails.problems(agent_post)))
        owner_post = self.post(text, made_by="owner")
        self.assertFalse(any("testimonial" in p for p in guardrails.problems(owner_post)))
        self.assertTrue(any("real reviews" in w for w in guardrails.warnings(owner_post)))
        # Once the owner has edited the agent's draft, it is the owner's words.
        agent_post.edited_by_owner = True
        self.assertFalse(any("testimonial" in p for p in guardrails.problems(agent_post)))

    def test_gifts_must_be_disclosed(self):
        undisclosed = self.post("Thanks to @tea.rina for trying our Assam!", gift=True)
        self.assertTrue(any("free gift" in p for p in guardrails.problems(undisclosed)))
        disclosed = self.post("We sent @tea.rina a tin of our Assam, free. #gifted", gift=True)
        self.assertEqual(guardrails.problems(disclosed), [])
        unmarked = self.post("Our favourite tea influencer tried the Assam.")
        self.assertTrue(any("influencer" in p for p in guardrails.problems(unmarked)))

    def test_no_personalised_prices(self):
        for text in ["A special price just for you.", "Because you bought Assam, here is your own discount.",
                     "Personalised offers on every tea."]:
            with self.subTest(text=text):
                self.assertTrue(any("same for everyone" in p for p in guardrails.problems(self.post(text))))

    def test_discount_codes_must_be_real_active_and_the_campaigns(self):
        code = DiscountCode.objects.create(code="AUTUMN10", value=Decimal("10"))
        campaign = Campaign.objects.create(name="Autumn", slug="autumn")
        text = "10% off our black teas with code AUTUMN10."
        self.assertTrue(any("doesn't belong" in p for p in guardrails.problems(self.post(text))))
        campaign.codes.add(code)
        self.assertEqual(guardrails.problems(self.post(text, campaign=campaign)), [])
        missing = self.post("Use code NOSUCH5 for a treat.", campaign=campaign)
        self.assertTrue(any("doesn't exist" in p for p in guardrails.problems(missing)))
        code.ends_on = timezone.localdate()
        code.save()
        later = self.post(text, campaign=campaign, scheduled_for=timezone.now() + timedelta(days=3))
        self.assertTrue(any("won't work then" in p for p in guardrails.problems(later)))

    def test_refund_promises_and_foreign_links_block(self):
        self.assertTrue(guardrails.problems(self.post("Not happy? We'll refund you, no questions.")))
        self.assertTrue(any("another site" in p for p in guardrails.problems(
            self.post("Read more at https://elsewhere.example/tea"))))

    def test_origin_and_organic_must_be_true(self):
        silver = catalog().__class__.objects.get(slug="silver-needle")
        problems = guardrails.problems(self.post("Fresh Darjeeling-style organic leaves.", product=silver))
        self.assertTrue(any("Darjeeling" in p for p in problems), problems)
        self.assertTrue(any("organic" in p.lower() for p in problems), problems)

    def test_network_limits_photos_and_time(self):
        long = self.post("Malty. " * 60, network="x")
        self.assertTrue(any("X allows 280" in p for p in guardrails.problems(long)))
        self.assertTrue(any("needs a photo" in p for p in guardrails.problems(self.post("Lovely.", "instagram"))))
        pin = self.post("Lovely.", "pinterest")
        self.assertTrue(any("needs a title" in p for p in guardrails.problems(pin)))
        self.assertTrue(any("no date" in p for p in guardrails.problems(self.post("Lovely.", scheduled_for=None))))

    def test_x_counts_links_as_23(self):
        post = self.post("a" * 250, network="x", link="/products/assam-second-flush/")
        self.assertEqual(post.length(), 250 + 1 + 23)
