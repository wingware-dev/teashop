# Architecture and conventions

## One Django app per feature

Each feature lives in its own app under `apps/`, so different phases can
be built side by side with few conflicts:

| App | Phase | Holds |
|---|---|---|
| `core` | 1 | Health check, owner dashboard shell, shared helpers, the design vocabulary (`design.py`) |
| `jobs` | — | The background job queue and its worker; see `docs/jobs.md` |
| `audit` | 1 | The audit log |
| `inventory` | 2 | Raw materials, lots, stock movements, bills of materials |
| `catalog` | 2, 3 | Products, size options, categories, regions, collections, photos, copy rules |
| `storefront` | 3 | Public pages (including the home page), page designs, tea notes, sitemap; see `docs/storefront.md` |
| `checkout` | 4 | Cart, orders, Stripe, shipping rates, tax, accounts, subscriptions; see `docs/checkout.md` |
| `fulfillment` | 5 | Order queue, packing records, labels, postage, refunds, pickups; see `docs/fulfillment.md` |

Names for later phases are suggestions; pick what fits.  To add an app:

1. `mkdir apps/<name>` and `python manage.py startapp <name> apps/<name>`.
2. In its `apps.py` set `name = "apps.<name>"` and `label = "<name>"`.
3. Add `"apps.<name>"` to `LOCAL_APPS` in `config/settings.py`, and its
   URLs to `config/urls.py` if it has pages.
4. Tests go in `apps/<name>/tests/`.

Rules between apps:

- `core` and `audit` depend on no feature app.  Feature apps may import
  them and each other's models, but avoid cycles: prefer signals or a
  small function in the lower app to reaching up.
- Back-office pages use `apps.core.decorators.owner_required`, which needs
  a two-factor sign-in by a staff user.
- Tests that need a signed-in owner use `apps.core.testing`
  (`make_owner`, `login_verified`).

## Browser tests

Every page gets a browser test in its app's `tests/test_ui.py`, built on
`apps.core.uitesting.BrowserTestCase`: `self.check_page(path, name)` (add
`signed_in=True` for back-office pages) opens it at phone and desktop
widths in the light and dark themes and fails on WCAG 2.2 AA violations
found by axe-core, JavaScript or HTTP errors, and sideways scrolling at
320 pixels; it saves screenshots to `var/shots/`.  For flows, drive the
page with Playwright (`self.new_page(...)`, `page.get_by_role(...)`) and
call `self.check_current(page, name)` at each step worth recording.
Look at the screenshots before calling a page done.  At the end of each
phase, `python manage.py milestone_shots <phase-name>` records them in
`doc/shots/`.

## The owner dashboard's "Needs your attention" list

core can't import feature apps, so each app registers a provider in its
`AppConfig.ready()` with `apps.core.attention.register(fn)`; `fn()` returns
a list of `Attention(title, detail, url, level)`.  A provider that raises
is logged and skipped.  inventory (low stock, best-by dates, lots on hold)
and catalog (organic sales limit, sizes that can't be packed) do this.
`register_shortcut(title, url_name)` adds a link to the dashboard's
Shortcuts card the same way (purchasing adds its reorder, losses and
profit pages).

## Purchasing (phase 7)

`apps/purchasing` holds stock counts, drafting purchase orders from
reorder levels, and the loss and profit reports.  The reorder math is in
`apps/inventory/reorder.py`, since inventory's low-stock alert uses it.
Purchase orders stay in inventory; `inventory.services.
approve_purchase_order()` is the only way a draft becomes ordered, and it
refuses AI agents.

## Inventory and catalog (phase 2)

See `docs/inventory.md` for how the owner uses them.  For other phases:

- Stock only changes through `apps.inventory.services` (`post_movement`,
  `adjust`, `consume`, `pick_lot`, `make_blend`), which lock the lot and
  record a `StockMovement`.  Movements are append-only.
- Fulfillment packs each package with `apps.catalog.services.pack(size,
  order_reference, tea_grams=...)`, which takes the bill of materials from
  stock, picks the tea lot (oldest best-by first, one lot per package)
  and returns a `SoldPackage`; `label_for(package)` gives the label facts.
  The order reference on its movements is what recall tracing
  (`apps.inventory.tracing`) reports.  `reverse_package(package, note)`
  undoes a pack (cancellations, mistakes) with "returned" movements.
- Storefront can show `SizeOption.packages_available()` for stock.
- Supplier documents use the `private` storage (`PRIVATE_MEDIA_ROOT`),
  which Caddy refuses to serve; the owner downloads them through
  `inventory:private_file`.  Product photos stay in public media.

## Settings

`config/settings.py` reads everything that differs between laptop and
server from environment variables (`.env.example` lists them).
`DJANGO_ENV=production` turns on the production checks: it refuses to
start without `DJANGO_SECRET_KEY` and `DATABASE_URL`, or with DEBUG on.

## Audit log

Every model change (create, update, delete) is recorded in
`audit.AuditEvent` automatically, with who did it, from which address, and
the changed fields.  Fields whose names contain password, secret, token or
key are masked.  Logins, logouts and failed logins are recorded too.
`settings.AUDIT_EXCLUDED_MODELS` and `AUDIT_IGNORED_FIELDS` leave out noise.

Who is acting comes from the request (the signed-in user) or from code:

```python
from apps.audit import acting_as_agent, record

with acting_as_agent("support-agent"):
    ...                                   # model changes credited to the agent
    record("support.reply_sent", obj=ticket, message="Order status answered")
```

Actions that are not model changes (a label bought, an email sent, a
backup restored) call `record()` with a dotted action name.  The log is
append-only: the model refuses changes, and on PostgreSQL a database
trigger does too.  The owner sees it in the dashboard and in the admin
(read-only).

## Payments: card data never touches the server

Checkout (phase 4) must use Stripe-hosted card fields (Stripe Checkout or
the Payment Element), so card numbers go from the customer's browser
straight to Stripe.  Never add a form field, model field or log line that
could hold a card number or security code.  This keeps the shop to PCI DSS
SAQ A, the shortest self-assessment.

## Background jobs

`apps/jobs` is a small job queue kept in PostgreSQL, run by the `worker`
service in `compose.yaml` (`manage.py run_jobs`): queued work, automatic
retries and daily or periodic jobs, with no other service to run.  All
emails go through it, as do the 6pm order summary and the renewal
reminders.  Anything slow or that may fail and should be retried (emails,
label purchases, agents) goes on it rather than in a request.  How to
declare, queue and schedule jobs: `docs/jobs.md`.  Use it rather than a
new systemd timer; systemd keeps only the backup timers, which run
outside the app.
