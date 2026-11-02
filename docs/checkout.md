# Cart, checkout, accounts and subscriptions

Phase 4 (`apps/checkout`): the cart, guest checkout, optional customer
accounts, Stripe payments, live USPS rates with address checking, New
York sales tax, discount codes, free shipping, order emails, vacation
mode, tea subscriptions, and the policy pages (`apps/storefront`).

## What customers see

1. **Product page:** size, quantity, "Add to cart".
2. **Cart** (`/cart/`): change quantities, remove, apply a discount code;
   it says how much more for free shipping.
3. **Address** (`/checkout/`): email and a US address.  EasyPost checks it
   with the post office; if the post office writes it differently the
   customer picks theirs or the corrected one.  Only the 48 contiguous
   states and DC (no Alaska, Hawaii, territories or APO/FPO).
4. **Shipping:** live USPS rates (Ground Advantage, Priority, Express;
   `SHIPPING_SERVICES`), the promised ship date, the total with tax.
5. **Payment:** Stripe's Payment Element: cards, Apple Pay, Google Pay,
   Link and whatever else is turned on in Stripe's dashboard.
6. **Done:** the order page (its link, with a secret in it, is in every
   email), then emails: the confirmation, and "shipped" with tracking.

**Accounts are optional.**  "Sign in" emails a link (no passwords to keep
or leak).  Signed in, a customer sees every order placed with their email
(guest ones too), uses "Buy again", saves their address and manages
subscriptions.

## Setting it up (you)

Checkout stays closed in production ("Online ordering opens soon") until
all of these are set in `.env`.  On a laptop, stand-ins take their place:
fixed shipping rates, and a "Pay (test)" button that moves no money.

- **Stripe** (stripe.com): `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`
  (use the **test** keys first).  Add a webhook endpoint at
  `https://<your domain>/checkout/stripe-webhook/` for
  `payment_intent.succeeded`, `invoice.paid`, `invoice.payment_failed`,
  `setup_intent.succeeded`, `customer.subscription.updated` and
  `customer.subscription.deleted`, and
  put its signing secret in `STRIPE_WEBHOOK_SECRET`.  For Apple Pay,
  register your domain under Settings → Payment method domains.  Live keys
  are refused until you set `STRIPE_ALLOW_LIVE=true`.
- **EasyPost** (easypost.com): `EASYPOST_API_KEY` (test key `EZTK...`
  first; a live key needs `EASYPOST_ALLOW_LIVE=true`) and the
  `SHIP_FROM_*` address.
- **Email:** `EMAIL_HOST` and friends, `DEFAULT_FROM_EMAIL`,
  `OWNER_NOTIFY_EMAIL` (new orders), `SHOP_CONTACT_EMAIL`,
  `SHOP_POSTAL_ADDRESS` (CAN-SPAM; a PO box is fine), `SITE_URL`.
- **Optional:** Cloudflare Turnstile keys for a bot check on checkout and
  sign-in.
- `manage.py check --deploy` warns about anything missing.

To try the Stripe code without an account, run stripe-mock
(`docker run -p 12111:12111 stripe/stripe-mock`) and set
`STRIPE_API_BASE=http://localhost:12111` with any `sk_test_` key.

## In the admin (Checkout)

- **Checkout settings:** free shipping from an amount (empty = none;
  decide yours), working days to ship (the FTC Mail Order Rule holds you to
  what customers are told), **vacation mode** (a notice on every page, and
  either orders ship from your return date or the checkout closes).
- **Discount codes:** percent, dollars, or free shipping; minimum order,
  dates, total uses, once per customer.  Codes are public, so prices stay
  the same for everyone.
- **Tax rates:** the combined New York rate per ZIP code (5 digits), ZIP
  area (first 3), or the whole state.  A ZIP with no rate is charged the
  highest NY rate (8.875%) and the dashboard lists it, so enter rates for
  where your customers are (NYS Publication 718 and the Tax Department's
  address lookup).  Or set `TAX_PROVIDER=stripe` to have Stripe Tax find
  the rate (about 0.5% per order).
- **Nexus thresholds:** each state's economic-nexus threshold, seeded
  from a 2025 summary; check a state's rule when the dashboard warns.
- **Orders:** entering a tracking number marks the order shipped and
  emails the customer.  Normally the packing pages (/owner/fulfillment/,
  `docs/fulfillment.md`) buy the label, which does this.
- **Subscription plans / subscriptions / customers.**

The dashboard's "Sales by state and sales tax" page shows New York tax
collected by quarter and sales into each state against its threshold.

## Sales tax

- Tea is exempt in New York (food); merchandise and accessories are taxed
  at the delivery address's rate.
- Tea-only orders: no tax, shipping included.  Mixed orders: shipping is
  split in proportion to the items' prices after discounts, and only the
  merchandise's share is taxed.  This is the safe method; confirm it with
  NYS Tax.  The split is always computed here (`apps/checkout/tax.py`);
  with Stripe Tax, only the rate comes from Stripe.
- Only states in `SALES_TAX_STATES` (NY) are charged.  Sales into every
  state are tracked against its threshold; the dashboard warns at 80%.

## Subscriptions (NY GBL 527-a, California's automatic renewal law)

- The renewal terms sit right next to the sign-up button, and a consent
  box must be ticked.  The text agreed to is kept with the subscription.
- After the first payment, an acknowledgment email gives the terms and
  how to cancel.
- Yearly terms get a reminder 15-45 days before each renewal, sent by the
  daily `subscription_reminders` job (`apps/checkout/jobs.py`, 14:00
  UTC, run by the job worker; see `docs/jobs.md`).  The dashboard flags a
  reminder that is late.
- Every subscription email has a one-step cancel link (no sign-in); so
  does the account page.  Cancelling stops all future charges.
- When a renewal payment fails, the email links to a card page
  (`/subscriptions/card/<token>/`, no sign-in, also on the account page):
  Stripe's card form saves a new card (a SetupIntent), it becomes the
  subscription's card, and the unpaid renewal is charged to it at once.
- No free trials.  A plan's price change applies to new subscribers only;
  to raise an existing subscriber's price, email them first.
- Deliveries are tea only (no sales tax), shipping included in the price.
  Each paid renewal becomes an order to pack.

## Bot and fraud protection

A hidden honeypot field, a time stamp (forms sent back too fast are
refused), a limit per visitor address per hour (`CHECKOUT_RATE_LIMIT`,
`SIGN_IN_RATE_LIMIT`), optional Cloudflare Turnstile, and Stripe Radar on
every payment.  Quantities are capped per size (`CART_MAX_QUANTITY`) and by
stock.  The rate limit lives in each web worker's memory, so the real limit
is that times the number of workers.

## Policies

`/policies/privacy/`, `terms`, `returns`, `shipping`, `subscriptions`,
`accessibility`, linked in every page's footer.  **They are a careful
draft, not legal advice: have a lawyer read them before opening.**  The
returns policy in particular is a choice (no returns of tea as food;
merch within 30 days; damaged or lost replaced or refunded): change it if
you want something else.  The privacy policy lists every service that
receives customer data (`apps/storefront/policies.py`, `PROCESSORS`); add
one there the day it starts.

## Content-Security-Policy

django-csp sends a strict policy (`config/settings.py`): our own scripts
and styles only, plus Stripe.js and its frames, and Turnstile.  Pages have
no inline scripts or styles; keep it so.  If Stripe's fields misbehave once
real keys are in, look in the browser console for blocked addresses and
add them; `CSP_REPORT_URI` collects such reports.

## For other phases

- Fulfillment (phase 5, `docs/fulfillment.md`) works from `Order` (status
  `paid`, `ship_by`) and calls `apps.checkout.orders.mark_shipped(order,
  tracking)`, which emails the customer.  It buys each label for the
  parcel actually packed (the rate quoted at checkout was for an
  estimated weight).  Refunds go through `payments.provider().refund()`.
- New-order emails to the owner come once a day in fulfillment's 6pm
  summary unless `OWNER_NEW_ORDER_EMAILS=each`.
- Sizes have an optional `shipping_grams` (catalog); without it the
  weight is estimated from the tea and package.
