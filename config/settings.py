"""Django settings for the teashop project.

Everything that differs between a laptop and the server comes from
environment variables (see .env.example).  DJANGO_ENV selects the mode:

- "dev" (the default): DEBUG on, SQLite under var/ unless DATABASE_URL is
  set, an insecure fixed SECRET_KEY.
- "production": DEBUG off, DJANGO_SECRET_KEY and DATABASE_URL required,
  HTTPS-only cookies, HSTS, and the proxy headers Caddy sets trusted.
"""

import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
VAR_DIR = BASE_DIR / "var"


def env_str(name, default=""):
    return os.environ.get(name, default).strip()


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    value = os.environ.get(name, "").strip()
    return int(value) if value else default


def env_list(name, default=()):
    value = os.environ.get(name, "")
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or list(default)


DJANGO_ENV = env_str("DJANGO_ENV", "dev")
if DJANGO_ENV not in ("dev", "production"):
    raise ImproperlyConfigured(f"DJANGO_ENV must be 'dev' or 'production', not {DJANGO_ENV!r}")
PRODUCTION = DJANGO_ENV == "production"

DEBUG = env_bool("DJANGO_DEBUG", default=not PRODUCTION)
if PRODUCTION and DEBUG:
    raise ImproperlyConfigured("DJANGO_DEBUG must not be on in production")

SECRET_KEY = env_str("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if PRODUCTION:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production")
    SECRET_KEY = "dev-only-insecure-key-never-use-in-production"

# The git commit the running code was built from, set by the Docker build.
GIT_SHA = env_str("GIT_SHA", "dev")

# localhost is always allowed so the container health check can reach the
# app directly; Caddy only forwards requests for the configured site.
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS") + ["localhost", "127.0.0.1"]
if not PRODUCTION:
    ALLOWED_HOSTS += ["[::1]", "testserver"]
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# --- Applications -----------------------------------------------------------
# One Django app per feature, under apps/.  Later phases add theirs to
# LOCAL_APPS (see docs/architecture.md).
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]
THIRD_PARTY_APPS = [
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    "axes",
    "csp",
]
LOCAL_APPS = [
    "apps.audit",
    "apps.core",
    "apps.jobs",
    "apps.inventory",
    "apps.catalog",
    "apps.storefront",
    "apps.purchasing",
    "apps.checkout",
    "apps.fulfillment",
    "apps.emaillist",
    "apps.reports",
    "apps.agents",
    "apps.support",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.AuditActorMiddleware",
    # Axes must be last so it sees the outcome of authentication.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.storefront.context_processors.storefront",
                "apps.checkout.context_processors.checkout",
            ],
        },
    },
]

# --- Database ---------------------------------------------------------------
DATABASE_URL = env_str("DATABASE_URL")
if not DATABASE_URL:
    if PRODUCTION:
        raise ImproperlyConfigured("DATABASE_URL must be set in production")
    DATABASE_URL = f"sqlite:///{VAR_DIR / 'dev.sqlite3'}"
    VAR_DIR.mkdir(exist_ok=True)
DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=60, conn_health_checks=True)}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Cache ------------------------------------------------------------------
# In the database, so the checkout rate limits (apps/checkout/protection.py)
# are shared by all gunicorn workers and survive restarts.  migrate creates
# the table (apps/checkout/apps.py runs createcachetable after it).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "teashop_cache",
        # Room for a burst of addresses without culling live counts.
        "OPTIONS": {"MAX_ENTRIES": 20000},
    }
}

# --- Authentication: owner login with two-factor, brute-force lockout -------
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "core:owner_dashboard"
LOGOUT_REDIRECT_URL = "storefront:home"
OTP_TOTP_ISSUER = env_str("OTP_TOTP_ISSUER", "Teashop")

# The owner admin lives at a non-default path in production to cut noise
# from scanners; it is still protected by two-factor login.
ADMIN_URL = env_str("DJANGO_ADMIN_URL", "admin/")
if not ADMIN_URL.endswith("/") or ADMIN_URL.startswith("/"):
    raise ImproperlyConfigured("DJANGO_ADMIN_URL must look like 'office/' (no leading slash, trailing slash)")

AXES_FAILURE_LIMIT = env_int("AXES_FAILURE_LIMIT", 5)
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "apps.core.net.client_ip"
AXES_LOCKOUT_TEMPLATE = "core/locked_out.html"

# Trust the X-Real-IP header only when Caddy sits in front and overwrites it.
TRUST_X_REAL_IP = env_bool("DJANGO_TRUST_X_REAL_IP", default=False)

# --- Internationalisation ---------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env_str("DJANGO_TIME_ZONE", "America/New_York")
USE_I18N = True
USE_TZ = True

# --- Static and media files -------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = VAR_DIR / "static"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = Path(env_str("DJANGO_MEDIA_ROOT", str(VAR_DIR / "media")))
# Supplier documents (spec sheets, certificates, packing slips) are kept
# out of the public media URL: Caddy refuses /media/private/, and the owner
# downloads them through an owner-only view.
PRIVATE_MEDIA_ROOT = Path(env_str("DJANGO_PRIVATE_MEDIA_ROOT", str(MEDIA_ROOT / "private")))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Stores under PRIVATE_MEDIA_ROOT.
    "private": {"BACKEND": "apps.inventory.storage.PrivateFileStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if PRODUCTION
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        )
    },
}

# --- Security headers and cookies -------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 12  # owner sessions last half a day
if PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r"^healthz$"]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Start at one day; raise to a year (31536000) once HTTPS is known good.
    SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 86400)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
    SECURE_HSTS_PRELOAD = False
    # HSTS for subdomains and the browser preload list are hard to undo, so
    # they are deliberate later decisions (docs/ops/README.md, "HTTPS").
    SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]

# Content Security Policy (django-csp): the browser runs only our own
# scripts and styles, plus Stripe's card fields (Stripe.js and its frames)
# and, when it is turned on, Cloudflare Turnstile's bot check.  Pages have
# no inline scripts or styles; the JSON-LD product data is not a script the
# browser runs, so it needs no exception.  CSP_REPORT_URI (optional) is
# where browsers report what the policy blocked.
from csp.constants import NONE, SELF  # noqa: E402

STRIPE_SCRIPT_SOURCES = ["https://js.stripe.com", "https://*.js.stripe.com"]
TURNSTILE_SOURCE = "https://challenges.cloudflare.com"
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF, *STRIPE_SCRIPT_SOURCES, TURNSTILE_SOURCE],
        "style-src": [SELF],
        "img-src": [SELF, "https://*.stripe.com"],
        "font-src": [SELF],
        "connect-src": [SELF, "https://api.stripe.com", "https://m.stripe.network", TURNSTILE_SOURCE],
        "frame-src": [*STRIPE_SCRIPT_SOURCES, "https://hooks.stripe.com", TURNSTILE_SOURCE],
        "frame-ancestors": [NONE],
        "form-action": [SELF],
        "base-uri": [SELF],
        "object-src": [NONE],
    },
}
# (Not kept as a CSP_* setting: django-csp 4 takes those for its old format.)
if env_str("CSP_REPORT_URI"):
    CONTENT_SECURITY_POLICY["DIRECTIVES"]["report-uri"] = [env_str("CSP_REPORT_URI")]

# --- Audit log --------------------------------------------------------------
# Models whose changes are not recorded: the log itself, and bookkeeping
# that would only add noise or is recorded another way.
AUDIT_EXCLUDED_MODELS = {
    "audit.auditevent",
    "migrations.migration",
    "admin.logentry",
    "sessions.session",
    "contenttypes.contenttype",
    "auth.permission",
    "axes.accessattempt",
    "axes.accesslog",
    "axes.accessfailurelog",
    # The job queue's bookkeeping; what jobs do is recorded as usual.
    "jobs.job",
    "jobs.schedule",
    # The dashboard queue's clock; reminders sent are recorded as emails.
    "core.attentionrecord",
    # Recorded as "agents.ai_call" with its cost.
    "agents.aiusage",
    # Messages hold the customer's words; "support.*" events record each
    # one received and sent.
    "support.message",
}
# Fields whose changes alone don't make an event ("*" applies to every model).
AUDIT_IGNORED_FIELDS = {
    "*": {"last_login"},
    "otp_totp.totpdevice": {"last_t", "throttling_failure_timestamp", "throttling_failure_count", "last_used_at"},
    "otp_static.staticdevice": {"throttling_failure_timestamp", "throttling_failure_count", "last_used_at"},
}

# --- Inventory, catalog and labels -----------------------------------------
# Warn on the dashboard this many days before a lot's best-by date.
INVENTORY_BEST_BY_WARNING_DAYS = env_int("INVENTORY_BEST_BY_WARNING_DAYS", 60)
# Selling organic products without certification is allowed up to this
# much a year; the dashboard warns from ORGANIC_SALES_ALERT on.
ORGANIC_EXEMPTION_LIMIT = env_int("ORGANIC_EXEMPTION_LIMIT", 5000)
ORGANIC_SALES_ALERT = env_int("ORGANIC_SALES_ALERT", 4000)
# The packer's name and address printed on every package label; use "\n"
# between lines.  A street address is required unless the business is
# listed in a current phone or city directory.
LABEL_PACKER_ADDRESS = env_str("LABEL_PACKER_ADDRESS").replace("\\n", "\n")

# --- Purchasing: reorder levels (apps/inventory/reorder.py) -----------------
# Use is measured over this many days (or since an item's first delivery,
# at least REORDER_MIN_HISTORY_DAYS).
REORDER_USAGE_WINDOW_DAYS = env_int("REORDER_USAGE_WINDOW_DAYS", 90)
REORDER_MIN_HISTORY_DAYS = env_int("REORDER_MIN_HISTORY_DAYS", 14)
# Defaults for items that don't set their own: extra stock kept as a buffer,
# and how many days of use each order covers.
REORDER_SAFETY_DAYS = env_int("REORDER_SAFETY_DAYS", 14)
REORDER_COVER_DAYS = env_int("REORDER_COVER_DAYS", 60)
# Lead time for a supplier that doesn't say, and for making a blend here.
REORDER_DEFAULT_LEAD_DAYS = env_int("REORDER_DEFAULT_LEAD_DAYS", 21)
BLEND_LEAD_DAYS = env_int("BLEND_LEAD_DAYS", 2)
# Origin names protected as certification marks or geographical
# indications.  Product names and copy may use them only for a product
# marked "Origin certified" (apps/catalog/copy_rules.py).  Verify the list
# with your suppliers; add names as you stock teas from such places.
CATALOG_PROTECTED_ORIGINS = env_list(
    "CATALOG_PROTECTED_ORIGINS",
    ["Darjeeling", "Nilgiri", "Kangra", "Assam Orthodox", "Longjing", "Dragon Well", "Uji"],
)

# --- Storefront -------------------------------------------------------------
# Until the shop opens, visitors see only the "coming soon" page and search
# engines are asked to stay away; the signed-in owner sees the whole shop
# to try it.  Opening the shop is the owner's decision: set
# STOREFRONT_OPEN=true in .env and redeploy.
STOREFRONT_OPEN = env_bool("STOREFRONT_OPEN", default=not PRODUCTION)
# The shop's name, until the real one is chosen and its trademark searched.
SHOP_NAME = env_str("SHOP_NAME", "Teashop")
# Where customers write to, and the postal address (a registered PO box is
# fine) that order emails and the policy pages show.  Use "\n" between
# lines.
SHOP_CONTACT_EMAIL = env_str("SHOP_CONTACT_EMAIL", "hello@example.com")
SHOP_POSTAL_ADDRESS = env_str("SHOP_POSTAL_ADDRESS").replace("\\n", "\n")
# The shop's address on the web, for links in emails.
SITE_URL = env_str("SITE_URL", "http://localhost:8000")
# The state whose law governs the terms of sale.
SHOP_STATE = "New York"

# --- Email ------------------------------------------------------------------
# Order emails, sign-in links and subscription notices.  Without
# EMAIL_HOST they are printed to the console (a laptop) instead of sent.
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", f"{SHOP_NAME} <orders@example.com>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST = env_str("EMAIL_HOST")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = env_int("EMAIL_PORT", 587)
    EMAIL_HOST_USER = env_str("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
    EMAIL_TIMEOUT = 20
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# Where new-order and problem notices for the owner go (empty: none).
OWNER_NOTIFY_EMAIL = env_str("OWNER_NOTIFY_EMAIL")
# New-order notices: "daily" (one summary from the send_order_summary job,
# at 6pm by its timer) or "each" (an email per order as it is paid).
OWNER_NEW_ORDER_EMAILS = env_str("OWNER_NEW_ORDER_EMAILS", "daily")
if OWNER_NEW_ORDER_EMAILS not in ("daily", "each"):
    raise ImproperlyConfigured("OWNER_NEW_ORDER_EMAILS must be 'daily' or 'each'")

# --- Owner dashboard queue and reports (apps/core/attention.py, apps/reports) --
# How long each kind of item in "Needs your attention" may wait before a
# reminder email, changing the defaults in apps/core/attention.py (KINDS):
# "0" at once, "30m", "4h", "3d", "daily" (in the daily reminder) or "HH:MM".
# E.g. ATTENTION_DEADLINES=support=0,refunds=2h,approvals=1d
ATTENTION_DEADLINES = dict(
    item.split("=", 1) for item in env_list("ATTENTION_DEADLINES") if "=" in item
)
# The daily reminder of everything waiting (New York time).
ATTENTION_DAILY_AT = env_str("ATTENTION_DAILY_AT", "08:00")

# Payment fees for orders whose fee Stripe has not reported (the stand-in
# payments, or before the fee is known): Stripe's standard US card rate.
PAYMENT_FEE_PERCENT = Decimal(env_str("PAYMENT_FEE_PERCENT", "2.9"))
PAYMENT_FEE_FIXED = Decimal(env_str("PAYMENT_FEE_FIXED", "0.30"))

# Wave (accounting): each day's sales summary is posted as one transaction
# on the Stripe clearing account (docs/reports.md).  WAVE_CLIENT "fake"
# keeps the entries here without calling Wave; "wave" uses Wave's API with
# WAVE_TOKEN (a full-access token) and WAVE_BUSINESS_ID.  WAVE_ACCOUNTS
# maps each line to a Wave account id: anchor (the Stripe clearing bank
# account), tea_sales, goods_sales, shipping_income, sales_tax, refunds,
# payment_fees, e.g. WAVE_ACCOUNTS=anchor=QWNj...,tea_sales=QWNj...
WAVE_CLIENT = env_str("WAVE_CLIENT", "fake")
if WAVE_CLIENT not in ("fake", "wave"):
    raise ImproperlyConfigured("WAVE_CLIENT must be 'fake' or 'wave'")
WAVE_TOKEN = env_str("WAVE_TOKEN")
WAVE_BUSINESS_ID = env_str("WAVE_BUSINESS_ID")
WAVE_ACCOUNTS = dict(item.split("=", 1) for item in env_list("WAVE_ACCOUNTS") if "=" in item)
WAVE_API_URL = env_str("WAVE_API_URL", "https://gql.waveapps.com/graphql/public")
# The first day sent to Wave: days before it are left to you (empty: the
# first day the daily job runs, yesterday).
WAVE_START_DATE = env_str("WAVE_START_DATE")

# Quarterly estimated tax: rough set-aside rates for income tax on the
# shop's profit, on top of self-employment tax.  Placeholders: set them
# with your tax preparer from your other income and last year's return.
ESTIMATED_TAX_FEDERAL_RATE = Decimal(env_str("ESTIMATED_TAX_FEDERAL_RATE", "0.12"))
ESTIMATED_TAX_STATE_RATE = Decimal(env_str("ESTIMATED_TAX_STATE_RATE", "0.055"))
# Social Security part of self-employment tax stops at this much of
# earnings (2026: $184,500; check each year).
SOCIAL_SECURITY_WAGE_BASE = Decimal(env_str("SOCIAL_SECURITY_WAGE_BASE", "184500"))

# --- Background jobs (apps/jobs, docs/jobs.md) -------------------------------
# Emails and daily jobs are queued in the database and run by the worker
# (manage.py run_jobs; the worker service in compose.yaml).  JOBS_EAGER
# runs a job as soon as it is queued, in the same process, so a laptop or a
# test needs no worker; it is off in production.
JOBS_EAGER = env_bool("JOBS_EAGER", default=not PRODUCTION)
# How often an idle worker looks for jobs.
JOBS_POLL_SECONDS = 3
# A job still "running" after this is taken to be lost with its worker and
# run again.
JOBS_STALE_AFTER = timedelta(minutes=30)
JOBS_KEEP_DONE = timedelta(days=14)
JOBS_KEEP_FAILED = timedelta(days=90)
# The worker touches this file each round; its healthcheck reads it.
JOBS_HEARTBEAT_FILE = env_str("JOBS_HEARTBEAT_FILE", "/tmp/teashop-worker.heartbeat")

# --- Checkout (apps/checkout, docs/checkout.md) -----------------------------
# Payments: Stripe's Payment Element (cards, Apple Pay, Google Pay, Link and
# more), card data never on this server.  Without STRIPE_SECRET_KEY a
# stand-in ("fake") takes the place of Stripe on a laptop and in tests; it
# never takes payments in production, where checkout stays closed until
# the Stripe keys are set.  Live keys (sk_live_...) are refused unless
# STRIPE_ALLOW_LIVE=true, so going live is a deliberate step.
STRIPE_SECRET_KEY = env_str("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = env_str("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = env_str("STRIPE_WEBHOOK_SECRET")
STRIPE_ALLOW_LIVE = env_bool("STRIPE_ALLOW_LIVE", False)
# Point at stripe-mock (http://localhost:12111) to try the Stripe code
# without an account.
STRIPE_API_BASE = env_str("STRIPE_API_BASE")
PAYMENT_PROVIDER = env_str("PAYMENT_PROVIDER", "stripe" if STRIPE_SECRET_KEY else "fake")
if PAYMENT_PROVIDER not in ("stripe", "fake"):
    raise ImproperlyConfigured("PAYMENT_PROVIDER must be 'stripe' or 'fake'")
if STRIPE_SECRET_KEY.startswith(("sk_live_", "rk_live_")) and not STRIPE_ALLOW_LIVE:
    raise ImproperlyConfigured("A live Stripe key is set: set STRIPE_ALLOW_LIVE=true to take real payments")

# Shipping: live USPS rates and address checking through EasyPost.  Without
# EASYPOST_API_KEY a stand-in with a fixed rate table is used (not in
# production).  Orders ship to the 48 contiguous states and DC only.
EASYPOST_API_KEY = env_str("EASYPOST_API_KEY")
SHIPPING_PROVIDER = env_str("SHIPPING_PROVIDER", "easypost" if EASYPOST_API_KEY else "fake")
if SHIPPING_PROVIDER not in ("easypost", "fake"):
    raise ImproperlyConfigured("SHIPPING_PROVIDER must be 'easypost' or 'fake'")
EASYPOST_ALLOW_LIVE = env_bool("EASYPOST_ALLOW_LIVE", False)
if EASYPOST_API_KEY and not EASYPOST_API_KEY.startswith("EZTK") and not EASYPOST_ALLOW_LIVE:
    raise ImproperlyConfigured("A production EasyPost key is set: set EASYPOST_ALLOW_LIVE=true to buy real postage")
# Where parcels ship from (the rates depend on it).
SHIP_FROM = {
    "name": env_str("SHIP_FROM_NAME", SHOP_NAME),
    "street1": env_str("SHIP_FROM_STREET1"),
    "street2": env_str("SHIP_FROM_STREET2"),
    "city": env_str("SHIP_FROM_CITY"),
    "state": env_str("SHIP_FROM_STATE", "NY"),
    "zip": env_str("SHIP_FROM_ZIP"),
    "phone": env_str("SHIP_FROM_PHONE"),
}
# USPS services offered at checkout (EasyPost's names).
SHIPPING_SERVICES = env_list("SHIPPING_SERVICES", ["GroundAdvantage", "Priority", "Express"])
# The box and filler around an order, added to the packages' weight.
SHIPPING_BOX_GRAMS = env_int("SHIPPING_BOX_GRAMS", 150)
# Weight of a packed size whose own shipping weight is not set: the tea
# plus this much for its package (teas), or this much (merchandise).
SHIPPING_PACKAGE_GRAMS = {"tin": 110, "pouch": 15, "box": 60, "": 30}
SHIPPING_DEFAULT_ITEM_GRAMS = env_int("SHIPPING_DEFAULT_ITEM_GRAMS", 450)

# Sales tax.  Collected only in the states listed here (where the shop is
# registered): New York to start.  Tea is exempt as food; merchandise and
# accessories are taxed at the destination's rate, and on a mixed order the
# shipping is split in proportion and only the taxable share is taxed.
# TAX_PROVIDER "table" uses the rates entered in the admin (Checkout → Tax
# rates); "stripe" asks Stripe Tax for the destination's rate.  A ZIP code
# with no rate in the table is charged SALES_TAX_FALLBACK_RATES and flagged
# on the dashboard, so the rate can be added.
SALES_TAX_STATES = env_list("SALES_TAX_STATES", ["NY"])
TAX_PROVIDER = env_str("TAX_PROVIDER", "table")
if TAX_PROVIDER not in ("table", "stripe"):
    raise ImproperlyConfigured("TAX_PROVIDER must be 'table' or 'stripe'")
SALES_TAX_FALLBACK_RATES = {"NY": "0.08875"}
# Warn on the dashboard when sales into a state reach this share of its
# economic-nexus threshold.
NEXUS_ALERT_SHARE = 0.8

# Bot protection: Cloudflare Turnstile on the checkout and sign-in forms
# when both keys are set (free; https://dash.cloudflare.com/?to=/:account/turnstile).
TURNSTILE_SITE_KEY = env_str("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET_KEY = env_str("TURNSTILE_SECRET_KEY")
# Form submissions allowed per visitor address per hour (checkout steps,
# sign-in links, discount codes).
CHECKOUT_RATE_LIMIT = env_int("CHECKOUT_RATE_LIMIT", 30)
SIGN_IN_RATE_LIMIT = env_int("SIGN_IN_RATE_LIMIT", 5)
# A form sent back sooner than this after the page was shown is refused
# (a person takes longer).
CHECKOUT_MIN_FORM_SECONDS = 2
# Most of one size in a cart, and most lines.
CART_MAX_QUANTITY = 12
CART_MAX_LINES = 30

# --- Fulfillment (apps/fulfillment, docs/fulfillment.md) ---------------------
# Shipping labels are bought through EasyPost (the key above); with a test
# key (EZTK...) they are test labels that cost nothing and never ship.
# Label format for the 4x6 thermal printer: "PDF" (print from the browser)
# or "ZPL" (Zebra-language printers that take raw files).
SHIPPING_LABEL_FORMAT = env_str("SHIPPING_LABEL_FORMAT", "PDF").upper()
if SHIPPING_LABEL_FORMAT not in ("PDF", "ZPL"):
    raise ImproperlyConfigured("SHIPPING_LABEL_FORMAT must be 'PDF' or 'ZPL'")
# The package (pouch or tin) label, in inches, "width x height".
PACKAGE_LABEL_SIZE = env_str("PACKAGE_LABEL_SIZE", "4x2")
# Outside sizes (inches: length, width, height) of a packed package whose
# size has no dimensions of its own (Fulfillment -> Package dimensions).
PACKAGE_DIMENSIONS_IN = {"tin": (3.0, 3.0, 4.5), "pouch": (5.5, 3.5, 1.5), "box": (4.0, 4.0, 4.0), "": (6.0, 6.0, 4.0)}
# Room for filler: a box must hold the packages' volume times this.
BOX_FILL_FACTOR = 1.3
# The Mail Order Rule: a delay longer than this past the promised date
# needs the customer's express consent, not just silence.
MAIL_ORDER_IMPLIED_CONSENT_DAYS = 30

# --- Email list (apps/emaillist, docs/emaillist.md) ---------------------------
# Marketing mailings, opt-in with a confirmation email.  They go out through
# a bulk sender (Amazon SES's SMTP interface is the recommended one) when
# EMAIL_LIST_EMAIL_HOST is set, else through EMAIL_HOST like order emails.
# Confirmation emails always go through EMAIL_HOST.
EMAIL_LIST_EMAIL_HOST = env_str("EMAIL_LIST_EMAIL_HOST")
EMAIL_LIST_EMAIL_PORT = env_int("EMAIL_LIST_EMAIL_PORT", 587)
EMAIL_LIST_EMAIL_HOST_USER = env_str("EMAIL_LIST_EMAIL_HOST_USER")
EMAIL_LIST_EMAIL_HOST_PASSWORD = env_str("EMAIL_LIST_EMAIL_HOST_PASSWORD")
# The From address of mailings: on the domain whose SPF, DKIM and DMARC the
# sender is set up for (Gmail's and Yahoo's bulk-sender rules).
EMAIL_LIST_FROM_EMAIL = env_str("EMAIL_LIST_FROM_EMAIL") or DEFAULT_FROM_EMAIL
# The List-Id header's identifier (RFC 2919): any stable dotted name.
EMAIL_LIST_ID = env_str("EMAIL_LIST_ID") or "news.teashop.example"
# Local time of the daily send to subscribers whose frequency now allows
# another email.  Approving a mailing also sends at once to those due.
EMAIL_LIST_SEND_AT = env_str("EMAIL_LIST_SEND_AT") or "10:00"
# How long a confirmation link works.
EMAIL_LIST_CONFIRM_WITHIN = timedelta(days=7)
# Sign-up form submissions allowed per visitor address per hour.
EMAIL_LIST_RATE_LIMIT = env_int("EMAIL_LIST_RATE_LIMIT", 10)

# --- AI agents (apps/agents, docs/agents.md) ----------------------------------
# Agents use a free stand-in that calls no AI service, unless named here
# (comma-separated, e.g. AGENTS_LIVE=support-agent): those call the Claude
# API with ANTHROPIC_API_KEY, which is billed by Anthropic per token.
AGENTS_LIVE = env_list("AGENTS_LIVE")
ANTHROPIC_API_KEY = env_str("ANTHROPIC_API_KEY")
if AGENTS_LIVE and not ANTHROPIC_API_KEY:
    raise ImproperlyConfigured("AGENTS_LIVE is set: set ANTHROPIC_API_KEY too, or empty AGENTS_LIVE")
AGENTS_MODEL = env_str("AGENTS_MODEL") or "claude-haiku-5-5"
# Dollars per million input and output tokens for AGENTS_MODEL, as
# "input,output".  Check them against Anthropic's price list.
_agent_prices = env_list("AGENTS_PRICE_PER_MTOK", ["1", "5"])
if len(_agent_prices) != 2:
    raise ImproperlyConfigured("AGENTS_PRICE_PER_MTOK must be 'input,output', e.g. 1,5")
AGENTS_PRICE_PER_MTOK = (Decimal(_agent_prices[0]), Decimal(_agent_prices[1]))
# The most all agents together may spend on AI in a calendar month
# (dollars).  At the cap they stop calling the AI and hand work to you.
AGENTS_MONTHLY_CAP = Decimal(env_str("AGENTS_MONTHLY_CAP") or "50")

# --- Customer support (apps/support, docs/support.md) -------------------------
# The support inbox the agent reads: "" (none: chat only) or "imap", with
# the mailbox's IMAP settings.  Customers write to SUPPORT_EMAIL (default
# SHOP_CONTACT_EMAIL), which replies come from.
SUPPORT_INBOX = env_str("SUPPORT_INBOX")
if SUPPORT_INBOX not in ("", "imap"):
    raise ImproperlyConfigured("SUPPORT_INBOX must be empty or 'imap'")
SUPPORT_IMAP_HOST = env_str("SUPPORT_IMAP_HOST")
SUPPORT_IMAP_PORT = env_int("SUPPORT_IMAP_PORT", 993)
SUPPORT_IMAP_USER = env_str("SUPPORT_IMAP_USER")
SUPPORT_IMAP_PASSWORD = env_str("SUPPORT_IMAP_PASSWORD")
SUPPORT_IMAP_FOLDER = env_str("SUPPORT_IMAP_FOLDER") or "INBOX"
if SUPPORT_INBOX == "imap" and not (SUPPORT_IMAP_HOST and SUPPORT_IMAP_USER and SUPPORT_IMAP_PASSWORD):
    raise ImproperlyConfigured("SUPPORT_INBOX=imap needs SUPPORT_IMAP_HOST, SUPPORT_IMAP_USER and SUPPORT_IMAP_PASSWORD")
SUPPORT_EMAIL = env_str("SUPPORT_EMAIL") or SHOP_CONTACT_EMAIL
# How often the inbox is read.
SUPPORT_POLL_MINUTES = env_int("SUPPORT_POLL_MINUTES", 2)
# Watch mode: a category is ready to answer on its own once this many of
# its latest drafts have been decided and at least SUPPORT_READY_RATE of
# them went out with no or small edits.  You turn it on.
SUPPORT_READY_MIN_DRAFTS = env_int("SUPPORT_READY_MIN_DRAFTS", 20)
SUPPORT_READY_RATE = float(env_str("SUPPORT_READY_RATE") or "0.9")
# Chat messages allowed per visitor address per hour, and agent runs per
# customer (email address) per day; past it, messages go to you unread by
# the agent (floods and mail loops cost nothing).
SUPPORT_CHAT_RATE_LIMIT = env_int("SUPPORT_CHAT_RATE_LIMIT", 30)
SUPPORT_AGENT_RUNS_PER_DAY = env_int("SUPPORT_AGENT_RUNS_PER_DAY", 15)

# --- Logging: everything to stdout, Docker rotates the files ----------------
LOG_LEVEL = env_str("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.db.backends": {"level": "INFO"},
    },
}

# --- Error tracking (optional; off unless SENTRY_DSN is set) ----------------
SENTRY_DSN = env_str("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env_str("SENTRY_ENVIRONMENT", DJANGO_ENV),
        release=GIT_SHA,
        send_default_pii=False,
        traces_sample_rate=0.0,
    )
