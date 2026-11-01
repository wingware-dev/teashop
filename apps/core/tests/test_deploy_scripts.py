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
