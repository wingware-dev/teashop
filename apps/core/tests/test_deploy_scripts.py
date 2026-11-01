"""The SSH forced command that limits the CI deploy key to "deploy <commit>"."""

import os
import subprocess
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
FORCED_COMMAND = ROOT / "deploy" / "server" / "ssh-deploy-command.sh"
SHA = "0123456789abcdef0123456789abcdef01234567"


class SshDeployCommandTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app_dir = Path(self.tmp.name)
        self.called = self.app_dir / "called.txt"
        fake_deploy = self.app_dir / "fake-deploy.sh"
        fake_deploy.write_text(f'#!/bin/sh\necho "$@" > "{self.called}"\n')
        fake_deploy.chmod(0o755)
        self.fake_deploy = fake_deploy

    def run_forced(self, requested):
        env = {
            **os.environ,
            "SSH_ORIGINAL_COMMAND": requested,
            "TEASHOP_APP_DIR": str(self.app_dir),
            "TEASHOP_DEPLOY_SCRIPT": str(self.fake_deploy),
        }
        return subprocess.run(["bash", str(FORCED_COMMAND)], env=env, capture_output=True, text=True, timeout=30)

    def test_deploys_full_commit_id(self):
        result = self.run_forced(f"deploy {SHA}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.called.read_text().strip(), SHA)

    def test_refuses_everything_else(self):
        for requested in (
            "",
            "bash",
            "deploy",
            "deploy 0123456",  # short ids could be ambiguous
            f"deploy {SHA}; rm -rf /",
            f"deploy {SHA}\nwhoami",
            f"deploy {SHA.upper()}",
            f"deploy  {SHA}",
            "deploy $(whoami)" + "0" * 30,
            f"rollback {SHA}",
        ):
            with self.subTest(requested=requested):
                result = self.run_forced(requested)
                self.assertEqual(result.returncode, 2)
                self.assertIn("refused", result.stderr)
                self.assertFalse(self.called.exists())


# A stand-in for docker: logs each call, answers "image inspect" as told by
# FAKE_HAVE_IMAGE, and plays the backup container from FAKE_JOB_OUTPUT and
# FAKE_JOB_STATUS.  The calls that record events only get logged.
FAKE_DOCKER = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$FAKE_DOCKER_LOG"
case "$*" in
    "image inspect "*) [ "${FAKE_HAVE_IMAGE:-1}" = 1 ] ;;
    *" record_ops_event "*) exit "${FAKE_RECORD_STATUS:-0}" ;;
    *" run --rm -T backup "*) printf '%s' "$FAKE_JOB_OUTPUT"; exit "${FAKE_JOB_STATUS:-0}" ;;
    *) exit 0 ;;
esac
"""


class OpsEventScriptTests(SimpleTestCase):
    """deploy/record-ops-event.sh and deploy/backup-job.sh, with a fake docker."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        docker = bin_dir / "docker"
        docker.write_text(FAKE_DOCKER)
        docker.chmod(0o755)
        self.docker_log = Path(self.tmp.name) / "docker.log"
        self.env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "FAKE_DOCKER_LOG": str(self.docker_log)}

    def run_script(self, name, *args, **env):
        return subprocess.run(
            ["bash", str(ROOT / "deploy" / name), *args],
            env={**self.env, **env}, capture_output=True, text=True, timeout=30,
        )

    def docker_calls(self):
        return self.docker_log.read_text().splitlines() if self.docker_log.exists() else []

    def record_call(self):
        calls = [call for call in self.docker_calls() if "record_ops_event" in call]
        self.assertEqual(len(calls), 1, self.docker_calls())
        return calls[0]

    def test_record_runs_management_command_in_current_build(self):
        result = self.run_script("record-ops-event.sh", "deploy", "succeeded", "--commit", "0123abcd4567")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            self.record_call(),
            "compose run --rm --no-deps -T web python manage.py record_ops_event deploy succeeded --commit 0123abcd4567",
        )

    def test_record_is_best_effort(self):
        result = self.run_script("record-ops-event.sh", "deploy", "failed", FAKE_HAVE_IMAGE="0")
        self.assertEqual(result.returncode, 0)
        self.assertIn("no teashop-web:current build", result.stdout)
        self.assertEqual([c for c in self.docker_calls() if "record_ops_event" in c], [])

        result = self.run_script("record-ops-event.sh", "deploy", "failed", FAKE_RECORD_STATUS="1")
        self.assertEqual(result.returncode, 0)
        self.assertIn("could not record deploy failed", result.stdout)

    def test_backup_success_is_recorded_with_snapshot(self):
        output = (
            "2026-11-01T03:15:00Z backup: uploading snapshot\n"
            "snapshot 1a2b3c4d saved\n"
            "2026-11-01T03:16:00Z backup: done\n"
        )
        result = self.run_script("backup-job.sh", "backup", FAKE_JOB_OUTPUT=output, FAKE_JOB_STATUS="0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("compose --profile ops run --rm -T backup backup.sh", self.docker_calls())
        self.assertIn("backup: done", result.stdout)  # the job's log still reaches the journal
        self.assertTrue(self.record_call().endswith(
            "record_ops_event backup succeeded --detail exit_status=0 --message Backup succeeded: snapshot 1a2b3c4d saved"
        ))

    def test_restore_test_failure_keeps_status_and_records_first_error(self):
        output = (
            "2026-11-01T05:00:00Z restore-test: restoring latest snapshot from b2:bucket:teashop\n"
            "2026-11-01T05:00:09Z restore-test: FAILED: snapshot has no database dump\n"
            "2026-11-01T05:00:09Z restore-test: FAILED\n"
        )
        result = self.run_script("backup-job.sh", "restore-test", FAKE_JOB_OUTPUT=output, FAKE_JOB_STATUS="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("compose --profile ops run --rm -T backup restore-test.sh", self.docker_calls())
        self.assertTrue(self.record_call().endswith(
            "record_ops_event restore_test failed --detail exit_status=1"
            " --message Restore test failed (exit status 1): FAILED: snapshot has no database dump"
        ))

    def test_backup_job_refuses_unknown_job(self):
        result = self.run_script("backup-job.sh", "everything")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.docker_calls(), [])
