"""The ops agent's pages in a real browser: phone and desktop, light and
dark, WCAG 2.2 AA checks, screenshots (see apps.core.uitesting).  The flow
approves a proposal and records the quarterly review as the owner would."""

from django.test import override_settings
from django.urls import reverse

from apps.core.uitesting import BrowserTestCase
from apps.ops import agent, review
from apps.ops.models import Proposal, QuarterlyReview

from .helpers import FakeServer


@override_settings(OPS_SERVER="demo")
class OpsUITests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        agent.upkeep(FakeServer())
        agent.check_health(FakeServer())

    def test_owner_home(self):
        self.check_page(reverse("ops:owner_home"), "ops-owner-home", signed_in=True)

    def test_review(self):
        self.check_page(reverse("ops:review"), "ops-review", signed_in=True)

    def test_dashboard_shows_the_agent(self):
        self.check_page(reverse("core:owner_dashboard"), "ops-dashboard", signed_in=True)

    def test_approve_and_review_flow(self):
        page = self.new_page("phone", "light", signed_in=True)
        page.goto(self.url(reverse("ops:owner_home")))
        reboot = Proposal.objects.get(key="reboot")
        card = page.locator(f"#proposal-{reboot.pk}")
        card.get_by_label("Note (optional)").fill("Sunday at 10pm")
        card.get_by_role("button", name="Approve").click()
        page.get_by_text("Approved: carry it out").wait_for()
        self.check_current(page, "ops-flow-approved")
        reboot.refresh_from_db()
        self.assertEqual(reboot.status, "approved")

        page.goto(self.url(reverse("ops:review")))
        for key, title, _ in review.ITEMS:
            page.get_by_label(title).check()
        page.get_by_role("button", name="Record the review").click()
        page.get_by_text("security review is recorded").wait_for()
        self.check_current(page, "ops-flow-review-done")
        self.assertEqual(QuarterlyReview.objects.get().checked, review.KEYS)
