from datetime import date, timedelta
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.core import attention
from apps.core.testing import login_verified, make_owner
from apps.ops import agent, alerts, review
from apps.ops.models import Proposal, QuarterlyReview, ServerReport

from .helpers import FakeServer


def owner_client(test):
    owner, device = make_owner()
    login_verified(test.client, owner, device)
    return owner


class PageTests(TestCase):
    def setUp(self):
        self.owner = owner_client(self)

    def test_pages_need_the_owner(self):
        self.client.logout()
        for name in ("ops:owner_home", "ops:review"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)

    @override_settings(OPS_SERVER="")
    def test_home_without_server(self):
        response = self.client.get(reverse("ops:owner_home"))
        self.assertContains(response, "Server checks are off on this computer")
        self.assertContains(response, "No reading yet")
        self.assertNotContains(response, "Check now")

    @override_settings(OPS_SERVER="demo")
    def test_home_with_readings_upkeep_and_proposals(self):
        agent.check_health(FakeServer())
        agent.upkeep(FakeServer())
        response = self.client.get(reverse("ops:owner_home"))
        self.assertContains(response, "Demo mode")
        self.assertContains(response, "Disk / is 88% full")
        self.assertContains(response, "Restart the server to finish installing updates")
        self.assertContains(response, "sudo reboot")
        self.assertContains(response, "strangers can write into")
        self.assertContains(response, "Installed security updates")

    @override_settings(OPS_SERVER="demo")
    def test_check_now_queues_a_check(self):
        response = self.client.post(reverse("ops:check_now"), follow=True)
        self.assertContains(response, "Checking the server")
        self.assertTrue(ServerReport.objects.filter(kind="health").exists())  # eager jobs on a laptop

    def test_decide_proposal(self):
        proposal = Proposal.objects.create(key="reboot", title="Restart", reason="r", steps="1. sudo reboot",
                                           proposed_by="ops-agent")
        url = reverse("ops:decide", args=[proposal.pk])
        self.client.post(url, {"action": "done"})
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, "open")  # not approved yet
        self.client.post(url, {"action": "approve", "note": "Sunday night"})
        proposal.refresh_from_db()
        self.assertEqual((proposal.status, proposal.note, proposal.decided_by), ("approved", "Sunday night",
                                                                                 self.owner))
        self.assertTrue(AuditEvent.objects.filter(action="ops.proposal_approved", actor_type="user").exists())
        self.client.post(url, {"action": "decline"})
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, "approved")
        self.client.post(url, {"action": "done"})
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, "done")
        self.assertEqual(self.client.get(url).status_code, 405)


class ReviewTests(TestCase):
    def setUp(self):
        self.owner = owner_client(self)

    def test_checklist_shows_facts(self):
        response = self.client.get(reverse("ops:review"))
        quarter = review.quarter_of(timezone.localdate())
        self.assertContains(response, f"Quarterly security review: {quarter}")
        self.assertContains(response, "two-factor on")  # the owner's account
        self.assertContains(response, "No restore test has succeeded yet")
        self.assertContains(response, "No server health reading yet")
        for _, title, _ in review.ITEMS:
            self.assertContains(response, title)

    def test_review_needs_every_item_or_a_note(self):
        response = self.client.post(reverse("ops:review"), {"item": review.KEYS[:3]})
        self.assertContains(response, "Tick each item, or say in the notes")
        self.assertFalse(QuarterlyReview.objects.exists())
        self.client.post(reverse("ops:review"), {"item": review.KEYS[:3], "notes": "No spare server for the rest."})
        done = QuarterlyReview.objects.get()
        self.assertEqual(done.checked, review.KEYS[:3])
        self.assertEqual(done.completed_by, self.owner)
        self.assertIn("updates", done.facts)
        event = AuditEvent.objects.get(action="ops.quarterly_review_succeeded")
        self.assertEqual(event.actor_type, "user")
        self.assertIn(f"{len(review.KEYS) - 3} items skipped", event.message)
        response = self.client.get(reverse("ops:review"))
        self.assertContains(response, "Done on")
        self.assertNotContains(response, "Record the review")

    def test_complete_review(self):
        self.client.post(reverse("ops:review"), {"item": review.KEYS + ["bogus"]})
        self.assertEqual(QuarterlyReview.objects.get().checked, review.KEYS)

    def test_due_after_the_first_month(self):
        self.assertFalse(review.due(date(2026, 10, 20)))
        self.assertTrue(review.due(date(2026, 11, 2)))
        self.assertTrue(review.due(date(2026, 12, 31)))
        QuarterlyReview.objects.create(quarter="2026-Q4")
        self.assertFalse(review.due(date(2026, 11, 2)))
        self.assertTrue(review.due(date(2027, 2, 1)))
        self.assertEqual(review.quarter_of(date(2027, 3, 31)), "2027-Q1")


class AttentionTests(TestCase):
    def titles(self):
        return [item.title for item in alerts.attention_items()]

    @override_settings(OPS_SERVER="")
    def test_findings_and_proposals(self):
        self.assertEqual(self.titles(), [])
        reading = FakeServer().run("health")
        reading["containers"] = reading["containers"][1:]  # no web container
        agent.check_health(FakeServer(reading))
        items = {item.title: item for item in alerts.attention_items()}
        web = items["Server: The web container is not running well (missing)"]
        self.assertEqual((web.kind, web.level), ("problems", "urgent"))
        self.assertEqual(items["Server: Disk / is 88% full"].kind, "other")
        self.assertFalse(any("journal" in title for title in items))  # info stays off the list
        proposal = Proposal.objects.create(key="reboot", title="Restart", reason="r", steps="s",
                                           proposed_by="ops-agent")
        self.assertIn("Server change to approve: Restart", self.titles())
        self.assertEqual([i.kind for i in alerts.attention_items() if "Restart" in i.title], ["approvals"])
        proposal.status = "approved"
        proposal.decided_at = timezone.now()
        proposal.save()
        self.assertIn("Approved server change to carry out: Restart", self.titles())

    @override_settings(OPS_SERVER="")
    def test_stale_or_failed_readings_stay_off_the_list(self):
        agent.check_health(FakeServer())
        ServerReport.objects.update(created_at=timezone.now() - timedelta(hours=4))
        self.assertEqual(self.titles(), [])
        with self.assertLogs("apps.ops.agent", "WARNING"):
            agent.check_health(FakeServer(fail={"health"}))
        self.assertEqual(self.titles(), [])

    def test_quarterly_review_only_on_the_server(self):
        with mock.patch("apps.ops.review.due", return_value=True):
            with override_settings(OPS_SERVER=""):
                self.assertEqual(self.titles(), [])
            with override_settings(OPS_SERVER="ssh"):
                self.assertTrue(any(t.startswith("Quarterly security review") for t in self.titles()))

    @override_settings(OPS_SERVER="")
    def test_registered_with_the_dashboard(self):
        Proposal.objects.create(key="k", title="Bigger disk", reason="r", steps="s", proposed_by="ops-agent")
        self.assertIn("Server change to approve: Bigger disk", [i.title for i in attention.collect()])
        self.assertIn(("Server health and security", reverse("ops:owner_home")), attention.shortcuts())
