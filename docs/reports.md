# Owner dashboard, reminders and reports (phase 6)

## "Needs your attention" and its deadlines

The dashboard (`/owner/`) lists everything waiting for you, grouped by
kind.  Each kind has a deadline; an item past it shows **Overdue** and
you get a reminder email at `OWNER_NOTIFY_EMAIL`:

| Kind | Holds | Reminder |
|---|---|---|
| Support escalations | Questions the support agent hands you (phase 9) | at once |
| Refunds and cancellations | Orders to cancel and refund (no answer to a delay notice) | after 4 hours |
| Things that are broken | Emails not going out, payments that don't match, no scale | after 1 hour |
| Failed jobs and backups | Background jobs that failed, worker stopped, backups, Wave posting | after 1 hour |
| Orders | Orders to pack, late or due, back-orders | the 6pm order summary |
| Posts and designs to approve | Page designs, mailings, social posts (phase 10) | after 3 days |
| Purchase orders | Drafts to approve, late deliveries | the daily reminder |
| Stock | Low stock, items at their reorder level, best-by dates, lots on hold | the daily reminder |
| Other | Sales-tax thresholds, organic limit, vacation mode, ... | the daily reminder |

- **The daily reminder** (8am New York time, `ATTENTION_DAILY_AT`) lists
  everything waiting, overdue first.  Nothing waiting: no email.
- **Overdue reminders** are checked every 5 minutes: one email for the
  items past their deadline, each item once.  After that it is in each
  daily reminder until it is dealt with.
- An item waits from when the app knows it began (a purchase order's
  draft date, a job's failure) or else from when the dashboard first
  listed it.  When it goes away and comes back, its clock starts again.
- Change a deadline with `ATTENTION_DEADLINES`, e.g.
  `ATTENTION_DEADLINES=refunds=2h,approvals=1d,stock=daily`
  (`0`, `30m`, `4h`, `3d`, `daily` or a time of day `HH:MM`).

For developers: a provider (see `docs/architecture.md`) gives each
`Attention` a `kind` (a key of `apps.core.attention.KINDS`), a `key` that
stays the same while the item is the same thing (no counts in it), and a
`since` when it knows one.  `attention.queue()` keeps the clock in
`core.AttentionRecord`; the reminders are in `apps/reports/reminders.py`
and their schedules in `apps/reports/jobs.py`.

## Reports (`/owner/reports/`)

- **Sales**: by day, week, month, quarter or year, and by channel (the
  shop, subscriptions), category and product.  Sales count the day the
  order was paid, refunds the day they were given; all without sales tax.
- **Margin**: net sales, cost of goods sold (landed cost of what was
  packed), gross margin, postage and Stripe fees, stock lost and samples,
  and stock on hand at landed cost.  Per tea, size and order:
  `/owner/purchasing/profit/`.
- **NY sales tax**: the figures for the return, for New York's quarters
  (March to May, June to August, September to November, December to
  February, due the 20th after) or the annual filer's year (March to
  February): sales delivered in New York, non-taxable (tea), taxable and
  tax by jurisdiction and rate, less refunds given in the period.  Look up
  each jurisdiction's reporting code in Publication 718.
- **Estimated tax**: profit to date per estimated-tax period (federal
  1040-ES and NY IT-2105 dates), self-employment tax on it, and an income
  tax set-aside at `ESTIMATED_TAX_FEDERAL_RATE` and
  `ESTIMATED_TAX_STATE_RATE` (placeholders: set them with your tax
  preparer).  Expenses kept only in Wave are not in the profit.

Stripe's fee is read from Stripe for each payment a few minutes after it
(`Order.payment_fee`); until then, and for the stand-in payments, reports
estimate it at `PAYMENT_FEE_PERCENT` + `PAYMENT_FEE_FIXED` and mark it.

## The daily summary for Wave

At 2:30am each day not yet sent (yesterday, or every day since
`WAVE_START_DATE`, at most 60) is posted to Wave as one deposit to the
Stripe clearing account: tea sales, merchandise sales, shipping and sales
tax, less refunds (and the tax they gave back) and Stripe's fees.  Each
day is sent once (and Wave's `externalId` stops a repeat).  A day Wave
refuses is kept as "Not posted", shown on the dashboard, and tried again
the next night; **Send them now** on `/owner/reports/accounting/` tries at
once.  Inventory bought is not posted: Wave's bank feed has the supplier
payments.

Until the shop has a Wave account, `WAVE_CLIENT=fake` (the default) keeps
the entries in the app only.  To connect:

1. In Wave, create accounts if missing: a bank-type "Stripe clearing"
   account, income accounts for tea sales, merchandise sales, shipping
   income and refunds (or "Sales returns"), the sales tax liability, and
   an expense account for payment processing fees.
2. Create a full-access token (Wave developer portal) and find the
   business id and each account's id (Wave's API playground:
   `businesses` and `accounts` queries).
3. Set `WAVE_CLIENT=wave`, `WAVE_TOKEN`, `WAVE_BUSINESS_ID` and
   `WAVE_ACCOUNTS=anchor=...,tea_sales=...,goods_sales=...,shipping_income=...,sales_tax=...,refunds=...,payment_fees=...`.
4. Set `WAVE_START_DATE` to the first day to send, and check the first
   day's transaction in Wave before letting it run on.

The client has been tested only against a stand-in for Wave's API, not
Wave itself: step 4 matters.
