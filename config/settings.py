"""Django settings for the teashop project.

Everything that differs between a laptop and the server comes from
environment variables (see .env.example).  DJANGO_ENV selects the mode:

- "dev" (the default): DEBUG on, SQLite under var/ unless DATABASE_URL is
  set, an insecure fixed SECRET_KEY.
- "production": DEBUG off, DJANGO_SECRET_KEY and DATABASE_URL required,
  HTTPS-only cookies, HSTS, and the proxy headers Caddy sets trusted.
"""

import os
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
]
LOCAL_APPS = [
    "apps.audit",
    "apps.core",
    "apps.inventory",
    "apps.catalog",
    "apps.storefront",
    "apps.purchasing",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
