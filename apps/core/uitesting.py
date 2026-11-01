"""Drive the site in a real browser, as its users will, and keep screenshots.

UI tests subclass ``BrowserTestCase``.  It starts Django's live server
(the development server, against the test database, with static files)
and a headless Chromium through Playwright.  ``check_page`` opens a page
at phone and desktop widths in the light and dark themes and, for each:

- fails on WCAG 2.2 AA violations found by axe-core,
- fails on JavaScript errors, failed requests and HTTP errors,
- fails if the page scrolls sideways at 320 CSS pixels (WCAG 1.4.10),
- saves a full-page screenshot.

Example::

    from apps.core.uitesting import BrowserTestCase

    class CatalogPagesUITests(BrowserTestCase):
        def test_product_list(self):
            self.check_page("/teas/", "teas-list")

        def test_stock_page(self):          # behind the two-factor login
            self.check_page("/owner/stock/", "owner-stock", signed_in=True)

        def test_add_to_cart(self):         # drive it by hand
            page = self.new_page("phone", "dark")
            page.goto(self.url("/teas/"))
            page.get_by_role("button", name="Add to cart").first.click()
            self.check_current(page, "cart-after-add")

Screenshots go to ``var/shots/`` (not kept in version control), named
``<name>-<viewport>-<theme>.png``.  To record a milestone in ``doc/shots/``
run ``python manage.py milestone_shots <milestone-name>``.

Needs ``pip install -r requirements-ui.txt`` and ``playwright install
chromium``; without them the tests are skipped with that advice.  All
UI tests are tagged ``ui``: ``manage.py test apps --tag ui`` runs only
them, ``--exclude-tag ui`` everything else.
"""

import os
import re
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, tag
from django.urls import reverse

from .testing import current_token, login_verified, make_owner, OWNER_PASSWORD

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - depends on the environment
    sync_playwright = None
    PlaywrightError = Exception

SKIP_ADVICE = (
    "Browser tests need Playwright: pip install -r requirements-ui.txt "
    "&& playwright install chromium"
)

VIEWPORTS = {
    "phone": {"width": 390, "height": 844},
    "desktop": {"width": 1280, "height": 800},
}
THEMES = ("light", "dark")

# WCAG 1.4.10 Reflow: content must fit 320 CSS pixels without sideways scrolling.
REFLOW_WIDTH = 320

# axe-core rule tags for WCAG 2.0, 2.1 and 2.2 at levels A and AA.
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"]

# Set by the milestone_shots command: screenshots go to doc/shots/<this>/.
MILESTONE_ENV = "TEASHOP_SHOTS_MILESTONE"
MILESTONE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def shots_dir():
    """Where screenshots of this run go: the milestone's folder in
    doc/shots/ when recording a milestone, else var/shots/."""
    milestone = os.environ.get(MILESTONE_ENV, "").strip()
    if milestone:
        if not MILESTONE_NAME_RE.match(milestone):
            raise ValueError(f"Bad milestone name {milestone!r}: use lowercase letters, digits, '.', '_' and '-'")
        return Path(settings.BASE_DIR) / "doc" / "shots" / milestone
    return Path(settings.VAR_DIR) / "shots"


def axe_script():
    """The axe-core script bundled with axe-playwright-python."""
    import axe_playwright_python

    return (Path(axe_playwright_python.__file__).parent / "axe.min.js").read_text(encoding="utf-8")


def format_violations(violations):
    """axe-core violations as readable lines, for test failure messages."""
    lines = []
    for violation in violations:
        lines.append(f"[{violation['impact']}] {violation['id']}: {violation['help']} ({violation['helpUrl']})")
        for node in violation["nodes"][:5]:
            lines.append(f"    {' '.join(node['target'])}: {node.get('failureSummary', '').splitlines()[-1].strip()}")
        if len(violation["nodes"]) > 5:
            lines.append(f"    ... and {len(violation['nodes']) - 5} more")
    return "\n".join(lines)


@tag("ui")
class BrowserTestCase(StaticLiveServerTestCase):
    """A live server plus a headless Chromium shared by the class's tests."""

    # Playwright's sync API runs an event loop in this thread, which makes
    # Django refuse database queries from test code (make_owner etc.)
    # unless told the thread is safe.  Only set while the class runs.
    _async_env_key = "DJANGO_ALLOW_ASYNC_UNSAFE"

    @classmethod
    def setUpClass(cls):
        if sync_playwright is None:
            cls._skip_reason = SKIP_ADVICE
        else:
            cls._skip_reason = None
        super().setUpClass()
        if cls._skip_reason:
            return
        cls._old_async_env = os.environ.get(cls._async_env_key)
        os.environ[cls._async_env_key] = "true"
        cls._playwright = sync_playwright().start()
        try:
            cls.browser = cls._playwright.chromium.launch()
        except PlaywrightError as exc:
            cls._playwright.stop()
            cls._restore_async_env()
            if "Executable doesn't exist" in str(exc):
                cls._skip_reason = SKIP_ADVICE
                return
            raise
        cls._axe_script = axe_script()

    @classmethod
    def tearDownClass(cls):
        if not cls._skip_reason:
            cls.browser.close()
            cls._playwright.stop()
            cls._restore_async_env()
        super().tearDownClass()

    @classmethod
    def _restore_async_env(cls):
        if cls._old_async_env is None:
            os.environ.pop(cls._async_env_key, None)
        else:
            os.environ[cls._async_env_key] = cls._old_async_env

    def setUp(self):
        if self._skip_reason:
            self.skipTest(self._skip_reason)
        super().setUp()
        self._contexts = []
        self._problems = {}

    def tearDown(self):
        for context in self._contexts:
            context.close()
        super().tearDown()

    # -- Pages ---------------------------------------------------------

    def url(self, path):
        return self.live_server_url + path

    def new_page(self, viewport="desktop", theme="light", signed_in=False):
        """A page in a fresh browser context (own cookies) at the given
        viewport ("phone" or "desktop") and theme ("light" or "dark").
        signed_in: sign in as the owner (two-factor passed) first."""
        context = self.browser.new_context(
            viewport=VIEWPORTS[viewport],
            color_scheme=theme,
            reduced_motion="reduce",
            device_scale_factor=2 if viewport == "phone" else 1,
            is_mobile=viewport == "phone",
            has_touch=viewport == "phone",
        )
        self._contexts.append(context)
        if signed_in:
            self.sign_in(context)
        page = context.new_page()
        problems = self._problems[page] = []
        page.on("pageerror", lambda exc: problems.append(f"JavaScript error: {exc}"))
        page.on(
            "console",
            lambda msg: problems.append(f"Console error: {msg.text}") if msg.type == "error" else None,
        )
        page.on("requestfailed", lambda req: problems.append(f"Request failed: {req.url} ({req.failure})"))
        page.on(
            "response",
            lambda resp: problems.append(f"HTTP {resp.status}: {resp.url}") if resp.status >= 400 else None,
        )
        return page

    # -- Signing in ----------------------------------------------------

    def owner(self):
        """The owner and their TOTP device, made on first use in each test."""
        if not hasattr(self, "_owner"):
            self._owner = make_owner()
        return self._owner

    def sign_in(self, context):
        """Give the browser context a signed-in owner session, two-factor
        already passed (fast; use sign_in_with_form to test the login)."""
        user, device = self.owner()
        client = Client()
        login_verified(client, user, device)
        session_cookie = client.cookies[settings.SESSION_COOKIE_NAME]
        context.add_cookies([{"name": session_cookie.key, "value": session_cookie.value, "url": self.live_server_url}])

    def sign_in_with_form(self, page, shot_prefix=None, owner=None):
        """Sign in through the real login pages: password, then the
        authenticator code.  shot_prefix: check and screenshot each step.
        owner: (user, device) from make_owner, else self.owner().  A code
        is accepted only once, so a second login within the same 30 seconds
        needs another owner."""
        user, device = owner or self.owner()
        page.goto(self.url(reverse("two_factor:login")))
        if shot_prefix:
            self.check_current(page, f"{shot_prefix}-password")
        page.get_by_label("Username").fill(user.username)
        page.get_by_label("Password").fill(OWNER_PASSWORD)
        page.get_by_role("button", name="Next").click()
        page.get_by_label("Token").wait_for()
        if shot_prefix:
            self.check_current(page, f"{shot_prefix}-code")
        page.get_by_label("Token").fill(current_token(device))
        page.get_by_role("button", name="Next").click()
        page.wait_for_load_state()

    # -- Checks --------------------------------------------------------

    def check_page(self, path, name, signed_in=False, viewports=None, themes=None):
        """Open path at each viewport and theme, check it and save a
        screenshot.  Returns nothing; fails the test on any problem."""
        for viewport in viewports or VIEWPORTS:
            for theme in themes or THEMES:
                with self.subTest(page=name, viewport=viewport, theme=theme):
                    page = self.new_page(viewport, theme, signed_in=signed_in)
                    response = page.goto(self.url(path))
                    self.assertIsNotNone(response, f"No response for {path}")
                    self.assertLess(response.status, 400, f"{path} answered HTTP {response.status}")
                    self.check_current(page, name, viewport=viewport, theme=theme)

    def check_current(self, page, name, viewport=None, theme=None):
        """Check the page as it is now and save its screenshot."""
        viewport = viewport or self._viewport_name(page)
        theme = theme or page.evaluate("matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'")
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        self.assert_no_page_problems(page)
        self.assert_accessible(page)
        self.assert_reflows(page)
        self.screenshot(page, f"{name}-{viewport}-{theme}")

    def assert_no_page_problems(self, page):
        problems = self._problems.get(page, [])
        if problems:
            self.fail(f"{page.url}:\n  " + "\n  ".join(problems))

    def assert_accessible(self, page):
        """No WCAG 2.2 A/AA violations that axe-core can detect.  axe finds
        perhaps a third of problems; it is a floor, not a certificate."""
        page.evaluate(self._axe_script)
        results = page.evaluate(
            "tags => axe.run(document, {runOnly: {type: 'tag', values: tags}, resultTypes: ['violations']})",
            WCAG_TAGS,
        )
        violations = results["violations"]
        if violations:
            self.fail(f"Accessibility problems on {page.url}:\n{format_violations(violations)}")

    def assert_reflows(self, page):
        """No sideways scrolling at 320 CSS pixels wide."""
        original = page.viewport_size
        page.set_viewport_size({"width": REFLOW_WIDTH, "height": original["height"]})
        try:
            overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        finally:
            page.set_viewport_size(original)
        self.assertLessEqual(overflow, 0, f"{page.url} scrolls sideways by {overflow}px at {REFLOW_WIDTH}px wide")

    def screenshot(self, page, filename):
        directory = shots_dir()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{filename}.png"
        page.screenshot(path=str(path), full_page=True, animations="disabled", caret="hide")
        return path

    @staticmethod
    def _viewport_name(page):
        width = page.viewport_size["width"]
        for name, size in VIEWPORTS.items():
            if size["width"] == width:
                return name
        return f"{width}px"
