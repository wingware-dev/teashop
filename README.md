# Teashop

The software for a small online specialty tea business: storefront,
inventory, fulfillment, back office and AI agents, built on Django and run
on one leased server.  `teashop.txt` describes the goals.

This is the phase 1 skeleton: the Django project, the owner's two-factor
login, the audit log, Docker, deployment, server hardening, backups and
the security documents.  The shop features come in later phases.

## Run it on your computer

Needs Python 3.13 or newer.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

In Wing, the Debug button runs the development server (the main entry
point, `manage.py runserver`); the named entry point "Migrate dev
database" applies migrations first.

Open http://127.0.0.1:8000/ (placeholder home page) and
http://127.0.0.1:8000/account/login/ to sign in.  The first sign-in takes
you to two-factor setup: scan the QR code with an authenticator app
(Google Authenticator, Authy, 1Password, ...), and save the backup codes.
After that, the owner dashboard is at /owner/ and the back office (Django
admin) at /admin/.

Development uses SQLite in `var/`; set `DATABASE_URL` to use PostgreSQL.

Run the tests with Wing's Testing tool or `python manage.py test apps`.

The browser tests (tagged `ui`) open each page in headless Chromium at
phone and desktop widths, in the light and dark themes, check it against
WCAG 2.2 AA with axe-core, and save screenshots to `var/shots/`.  They
need, once:

```sh
.venv/bin/pip install -r requirements-ui.txt
.venv/bin/playwright install chromium
```

Without them those tests are skipped.  `--exclude-tag ui` leaves them
out; `python manage.py milestone_shots <name>` records a milestone's
screenshots in `doc/shots/` (see `doc/shots/README.md`).

## Run the whole stack locally (as on the server)

Needs Docker.  Copy `.env.example` to `.env` and set, for a local trial:

```
SITE_DOMAIN=localhost
HTTP_PORT=8080
HTTPS_PORT=8443
CSRF_TRUSTED_ORIGINS=https://localhost:8443
```

plus random values for `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` and
`RESTIC_PASSWORD`.  Then commit your work and run `deploy/deploy.sh`.  The
site is at https://localhost:8443/ (your browser will warn about Caddy's
local certificate).

## Where things are

| Path | What |
|---|---|
| `config/` | Django settings (all from environment variables) and URLs |
| `apps/` | One Django app per feature; see `docs/architecture.md` |
| `apps/core/` | Home page, health check, owner dashboard, shared helpers |
| `apps/audit/` | Append-only log of admin, agent and system actions |
| `templates/`, `static/` | Site-wide templates and styles |
| `compose.yaml`, `Dockerfile` | The server stack: PostgreSQL, the app, Caddy, backups |
| `deploy/` | Deploy, rollback, backup and server setup scripts |
| `.github/workflows/` | CI on every push; deploy on push to `release` |
| `docs/ops/` | Running the server: setup, deploys, backups, monitoring |
| `docs/security/` | Security policy (NY SHIELD Act) and breach response checklist |
