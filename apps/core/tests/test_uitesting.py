"""The browser-test harness's own helpers (no browser needed)."""

import io
import os
import shutil
import struct
import zlib
from pathlib import Path
from unittest import mock, skipUnless

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from apps.core.management.commands import milestone_shots
from apps.core.uitesting import MILESTONE_ENV, format_violations, shots_dir


class ShotsDirTests(SimpleTestCase):
    def test_var_shots_by_default(self):
        with mock.patch.dict(os.environ, {MILESTONE_ENV: ""}):
            self.assertEqual(shots_dir(), Path(settings.VAR_DIR) / "shots")

    def test_milestone_goes_to_doc_shots(self):
        with mock.patch.dict(os.environ, {MILESTONE_ENV: "2026-11-01-phase1"}):
            self.assertEqual(shots_dir(), Path(settings.BASE_DIR) / "doc" / "shots" / "2026-11-01-phase1")

    def test_milestone_name_cannot_leave_doc_shots(self):
        for bad in ("../escape", "/abs", "Has Spaces", ".hidden"):
            with self.subTest(bad=bad), mock.patch.dict(os.environ, {MILESTONE_ENV: bad}):
                with self.assertRaises(ValueError):
                    shots_dir()


class MilestoneShotsCommandTests(SimpleTestCase):
    def test_rejects_bad_name_before_running_anything(self):
        with mock.patch("apps.core.management.commands.milestone_shots.call_command") as run_tests:
            with self.assertRaises(CommandError):
                call_command("milestone_shots", "../oops")
        run_tests.assert_not_called()

    def test_failed_tests_leave_no_shots_and_restore_env(self):
        def failing_tests(*args, **kwargs):
            directory = shots_dir()
            directory.mkdir(parents=True)
            (directory / "home-phone-light.png").write_bytes(b"")
            raise SystemExit(1)

        doc_shots = Path(settings.BASE_DIR) / "doc" / "shots" / "2000-01-01-harness-selftest"
        self.addCleanup(lambda: doc_shots.exists() and doc_shots.rmdir())
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(MILESTONE_ENV, None)
            with mock.patch("apps.core.management.commands.milestone_shots.call_command", side_effect=failing_tests):
                with self.assertRaises(CommandError):
                    call_command("milestone_shots", "harness-selftest", "--date", "2000-01-01")
            self.assertNotIn(MILESTONE_ENV, os.environ)
        self.assertFalse(doc_shots.exists())

    @skipUnless(milestone_shots.oxipng, "needs pip install -r requirements-ui.txt")
    def test_compresses_shots(self):
        # A deliberately badly compressed PNG: 200x200 of one colour, stored.
        width = height = 200
        raw = b"".join(b"\x00" + b"\x40\x80\xc0" * width for _ in range(height))

        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

        png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw, 0)) + chunk(b"IEND", b""))

        def passing_tests(*args, **kwargs):
            directory = shots_dir()
            directory.mkdir(parents=True)
            (directory / "home-phone-light.png").write_bytes(png)

        doc_shots = Path(settings.BASE_DIR) / "doc" / "shots" / "2000-01-01-harness-selftest"
        self.addCleanup(shutil.rmtree, doc_shots, ignore_errors=True)
        out = io.StringIO()
        with mock.patch("apps.core.management.commands.milestone_shots.call_command", side_effect=passing_tests):
            call_command("milestone_shots", "harness-selftest", "--date", "2000-01-01", stdout=out)
        shot = (doc_shots / "home-phone-light.png").read_bytes()
        self.assertTrue(shot.startswith(b"\x89PNG"))
        self.assertLess(len(shot), len(png) // 10)
        self.assertIn("1 screenshots", out.getvalue())


class FormatViolationsTests(SimpleTestCase):
    def test_lists_rule_and_elements(self):
        text = format_violations([
            {
                "id": "color-contrast",
                "impact": "serious",
                "help": "Elements must meet minimum color contrast ratio thresholds",
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.12/color-contrast",
                "nodes": [{"target": ["p.muted"], "failureSummary": "Fix any of the following:\n  contrast is 3.1:1"}],
            }
        ])
        self.assertIn("[serious] color-contrast", text)
        self.assertIn("p.muted: contrast is 3.1:1", text)
