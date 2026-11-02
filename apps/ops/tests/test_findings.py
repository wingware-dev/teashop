from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from django.test import SimpleTestCase

from apps.ops import findings as rules
from apps.ops.server import DemoServer

from .helpers import healthy

NOW = datetime(2026, 11, 1, 12, tzinfo=dt_timezone.utc)


def keys(found):
    return {finding.key: finding for finding in found}


class AssessTests(SimpleTestCase):
    def test_healthy_server_has_nothing_serious(self):
        found = rules.assess(healthy())
        self.assertEqual([f for f in found if f.level != rules.INFO], [])
        self.assertEqual(rules.summary(found), "All is well")

    def test_demo_reading(self):
        found = keys(rules.assess(DemoServer().run("health")))
        self.assertEqual(found["disk:/"].level, rules.WARNING)
        self.assertEqual(found["disk:/"].fix, "rotate_logs")
        self.assertEqual(found["disk:/"].proposal.key, "disk:/")
        self.assertEqual(found["updates:security"].fix, "apply_security_updates")
        self.assertEqual(found["updates:security"].level, rules.WARNING)  # automatic run 3 days ago
        self.assertEqual(found["reboot"].proposal.key, "reboot")
        self.assertEqual(found["journal"].fix, "rotate_logs")

    def test_thresholds(self):
        reading = healthy()
        reading["disks"][0]["used_percent"] = 96
        reading["memory"].update(total_mb=4000, available_mb=300)
        reading["load"] = [9.0, 9.0, 9.0]
        found = keys(rules.assess(reading, NOW))
        self.assertEqual(found["disk:/"].level, rules.URGENT)
        self.assertIn("memory", found)
        self.assertIn("load", found)
        self.assertEqual(rules.assess(reading, NOW)[0].level, rules.URGENT)  # worst first

    def test_recent_security_updates_wait_for_the_automatic_run(self):
        reading = healthy()
        reading["updates"].update(pending=2, security=2, last_automatic_run=int(NOW.timestamp()) - 3600)
        self.assertEqual(keys(rules.assess(reading, NOW))["updates:security"].level, rules.INFO)

    def test_updates_not_running_are_proposed(self):
        reading = healthy()
        reading["updates"]["last_automatic_run"] = int((NOW - timedelta(days=5)).timestamp())
        self.assertEqual(keys(rules.assess(reading, NOW))["updates:late"].proposal.key, "updates:late")
        reading["updates"]["security"] = None
        self.assertIn("updates:unknown", keys(rules.assess(reading, NOW)))

    def test_many_other_updates_are_proposed(self):
        reading = healthy()
        reading["updates"]["pending"] = 30
        self.assertEqual(keys(rules.assess(reading, NOW))["updates:other"].proposal.risk, "medium")

    def test_recent_reboot_waits_for_tonight(self):
        reading = healthy()
        reading["reboot_required"] = {"since": int(NOW.timestamp()) - 3600, "packages": ["linux-base"]}
        finding = keys(rules.assess(reading, NOW))["reboot"]
        self.assertEqual(finding.level, rules.INFO)
        self.assertIsNone(finding.proposal)

    def test_containers_and_failed_units(self):
        reading = healthy()
        reading["containers"] = [c for c in reading["containers"] if "worker" not in c["name"]]
        reading["containers"][0]["state"] = "unhealthy"
        reading["failed_units"] = ["teashop-backup.service"]
        found = keys(rules.assess(reading, NOW))
        self.assertEqual(found["container:worker"].level, rules.URGENT)
        self.assertEqual(found["container:web"].level, rules.URGENT)
        self.assertIn("systemctl status teashop-backup.service", found["units:teashop-backup.service"].proposal.steps)
        reading["containers"] = None
        self.assertIn("containers:unknown", keys(rules.assess(reading, NOW)))

    def test_ubuntu_support_end(self):
        reading = healthy()
        self.assertNotIn("os:24.04", keys(rules.assess(reading, NOW)))
        late = datetime(2028, 12, 1, tzinfo=dt_timezone.utc)
        finding = keys(rules.assess(reading, late))["os:24.04"]
        self.assertEqual((finding.level, finding.proposal.risk), (rules.WARNING, "high"))
        reading["os"] = {"name": "Debian 12", "id": "debian", "version": "12"}
        self.assertIn("os:unknown", keys(rules.assess(reading, NOW)))

    def test_summary_lists_worst_three(self):
        found = [rules.Finding(rules.WARNING, str(n), f"Problem {n}") for n in range(5)]
        self.assertEqual(rules.summary(found), "Problem 0; Problem 1; Problem 2; and 2 more")


class AssessLogsTests(SimpleTestCase):
    def test_logs(self):
        found = keys(rules.assess_logs(DemoServer().run("logs")))
        self.assertIn("owner from 203.0.113.7 (2)", found["ssh:logins"].detail)
        self.assertEqual(found["ssh:failed"].level, rules.INFO)
        self.assertIn("log:web", found)
        self.assertNotIn("web:errors", found)

    def test_many_server_errors_warn(self):
        logs = {"sources": {"caddy": {"requests": 100, "server_errors": 40}}, "unreadable": {"db": "refused"}}
        found = keys(rules.assess_logs(logs))
        self.assertEqual(found["web:errors"].level, rules.WARNING)
        self.assertIn("log:db:unreadable", found)
