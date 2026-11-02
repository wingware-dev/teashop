# The email list (phase 8)

`apps/emaillist` keeps the shop's own marketing email list: who signed
up, the record of their consent, how often each wants to hear from us,
and the mailings you write and approve.  A bulk email service only
**sends** the emails (see "Choosing the sending service" below).

## How it works for a customer

1. **Signing up** is opt-in only.  The "Email news" page
   (`/email-list/`, linked at the foot of every shop page) asks for an
   email address and **how often, at most**: once a week, once every two
   weeks, or once a month (the default).  Nothing else on the site signs
   anyone up, and checkout's email field says "No marketing unless you ask
   for it".
2. **Confirming.**  We email a link; the person opens it and presses
   "Yes, sign me up".  Until then they get nothing else.  The link works
   for 7 days.  Opening it alone does nothing, so mail scanners that
   follow links can't sign anyone up.
3. **Every mailing** has, at its foot, why they get it, a link to change
   how often, a link to unsubscribe, and the shop's postal address.  It
   also carries the `List-Unsubscribe` and `List-Unsubscribe-Post`
   headers, so Gmail, Yahoo and Apple Mail show their own "Unsubscribe"
   button, which takes them off the list in one click (RFC 8058).
4. **Unsubscribing** takes effect at once.  The link in the email shows
   one button (again so link scanners can't unsubscribe anyone); the mail
   apps' own button needs none.

Signing up again after unsubscribing needs a new confirmation.  Someone
already on the list who fills in the form gets an email with their
settings link, and nothing changes, so the form can't be used to change
someone else's settings or to learn who is on the list.  The form has
the same bot checks as checkout (honeypot, timing, rate limits,
Turnstile when set up) and sends at most three confirmation emails to one
address an hour.

## Consent records

Each step (asked to join, confirmed, changed how often, unsubscribed,
removed by you) is a **consent record** with the time, the visitor's
address and browser, the email address and frequency, and for sign-ups
the exact words the form showed.  They can't be changed or deleted, and
subscribers can't be deleted either (admin → Email list → Subscribers),
so the proof that the list is opt-in stays.  To take someone off (they
asked by email, the address bounces, they complained) use the admin
action "Take off the list".

## Writing and approving mailings

Owner pages: Dashboard → Shortcuts → "Email list and mailings"
(`/owner/email-list/`).

1. **Write a mailing**: a subject, the text (plain text, a blank line
   between paragraphs) and, for news that goes stale like a sale, the
   last day it may be sent.  Saving keeps it a **draft**.  A marketing
   agent can draft mailings too (`services.draft_mailing`).
2. The draft's page shows it **as a subscriber sees it**.  Each draft is
   on the dashboard's "Needs your attention" list as an approval.
3. **Approve and send.**  Only you can: AI agents can draft but never
   approve, and nothing reaches the list without approval.  Approval is
   refused until the shop's postal address is set.  Check that the subject
   says honestly what is inside (CAN-SPAM forbids misleading subjects).
4. It goes at once to every confirmed subscriber who is **due** an email,
   and to each of the others **as soon as their chosen frequency
   allows**, at 10:00 each morning (`EMAIL_LIST_SEND_AT`).
5. **Withdraw** stops an approved mailing going to anyone else.

### How the frequency limit combines mailings

Each subscriber may get one email per 7, 14 or 30 days.  When they are
due, everything approved since their last email (and since they joined:
no back issues) goes in **one** email, the newest first, under the
newest mailing's subject with ", and 2 more updates" added.  A mailing
past its last day is left out.  So you can approve as often as you like:
weekly subscribers hear weekly, monthly ones get a monthly digest.

## Sending

Each email is its own job on the job queue (`apps.jobs`, docs/jobs.md),
queued with a key, so each retries on its own for about 18 hours before
it shows as failed on the dashboard.  The daily send is a job schedule
(`apps/emaillist/jobs.py`), not a systemd timer.  An email still queued
when the subscriber leaves, or whose mailings were all withdrawn, is
skipped.  The dashboard flags emails unsent after 30 minutes, and a
missing postal address.

Settings (`.env`, see `.env.example`):

| Setting | What |
|---|---|
| `EMAIL_LIST_EMAIL_HOST`, `_PORT`, `_HOST_USER`, `_HOST_PASSWORD` | The bulk sender's SMTP interface (STARTTLS).  Empty: mailings go through `EMAIL_HOST` like order emails. |
| `EMAIL_LIST_FROM_EMAIL` | The From address, e.g. `Teashop <news@yourshop.com>`, on the domain the sender is set up for. |
| `EMAIL_LIST_ID` | The `List-Id` header, any stable dotted name (`news.yourshop.com`). |
| `EMAIL_LIST_SEND_AT` | Local time of the daily send, default `10:00`. |
| `SHOP_POSTAL_ADDRESS` | Required for mailings: a registered PO box will do. |

Confirmation and "already subscribed" emails always go through
`EMAIL_HOST` with the order emails.

## Choosing the sending service

Checked against the providers' own pages in November 2026.  Nothing has
been signed up for.

| | Amazon SES | Postmark (Broadcast stream) | Zoho |
|---|---|---|---|
| Cost at ~10,000 emails a month | about $1 ($0.10 per 1,000, no minimum) | $15-18 a month | — |
| Marketing email allowed | Yes (say "Marketing" when asking for production access) | Yes, on a separate Broadcast stream, after Postmark approves it | Zoho Mail and ZeptoMail **forbid** it; only Zoho Campaigns allows it |
| Works with our own list | Yes: SMTP, our headers and links | Yes, but by default Postmark adds its own unsubscribe link and headers and keeps its own unsubscribe list; using ours needs their support's approval | Campaigns sends only to lists kept in Zoho, with no SMTP relay |
| Getting started | New accounts are in a "sandbox" (only to verified addresses, 200 a day) until a production-access request is approved, usually within a day or so | Account approval for broadcasts | — |

**Recommendation: Amazon SES**, through its SMTP interface (the settings
above).  It is the cheapest by far, sends exactly the message this app
builds (our unsubscribe link and headers, so our consent records stay the
only list), and needs no code beyond SMTP.  Postmark is the
easier-to-run alternative with a better reputation for hand-holding, at
about $15 a month, but its unsubscribe handling would have to be either
switched off (by request) or synced back.  **Zoho doesn't fit:** Zoho
Mail's and ZeptoMail's terms forbid marketing and newsletters (ZeptoMail
blocks accounts that send them), and Zoho Campaigns would mean keeping
the list, consent and frequency limits in Zoho instead of here.  Zoho
Mail can stay the shop's mailbox.

### Setting up SES (when you are ready)

1. In the AWS console, SES, pick one region (e.g. us-east-1) and
   **verify your domain** with Easy DKIM: add the three CNAME records it
   gives to your DNS.
2. Set a **custom MAIL FROM domain** (e.g. `bounce.yourshop.com`: an MX
   and an SPF TXT record), so SPF aligns with your From domain.
3. **DMARC**: add a TXT record at `_dmarc.yourshop.com`, starting with
   `v=DMARC1; p=none; rua=mailto:you@yourshop.com` and tightening to
   `p=quarantine` once reports look clean.  If Zoho Mail sends your
   everyday mail, keep its SPF include in the same SPF record.
4. Request **production access**: mail type Marketing, the shop's URL,
   and that you send only to people who confirmed, with one-click
   unsubscribe, and remove bounces and complaints.
5. Create **SMTP credentials** (SES → SMTP settings) and put the host
   (`email-smtp.<region>.amazonaws.com`), port 587, user and password in
   `.env` as `EMAIL_LIST_EMAIL_*`, with `EMAIL_LIST_FROM_EMAIL` on the
   verified domain.  Redeploy.
6. Send a mailing to yourself first (sign up with your own address).

Gmail's and Yahoo's bulk-sender rules (SPF, DKIM and DMARC aligned with
the From domain; one-click unsubscribe; an unsubscribe link in the text;
spam complaints under 0.3%) are met by steps 1-3 and this app.  Bounces
and complaints are not yet read back automatically: until they are, SES
emails them to the From address, and you take those people off with the
admin action.  Watch SES's reputation page: SES pauses accounts whose
bounce or complaint rates run high.
