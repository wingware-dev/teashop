# Customer support (`apps/support`)

Customers reach the shop by the **chat** ("Chat with us" at the foot of
every page, `/help/chat/`) and by **email** to `SUPPORT_EMAIL`.  The AI
support agent reads each message at once, day and night, and answers only
clear-cut questions:

- **order status and tracking**: with the order number, and only when the
  order's email is the customer's;
- **brewing advice** for a tea the shop sells, from the catalog's brewing
  facts;
- **shipping times and costs**, from the checkout settings and USPS's
  usual times in transit.

Everything else (refunds, returns, damage, complaints, allergies and health
questions, discounts, wholesale, anything unclear) goes to you at once: the
customer is told "we'll get back to you", the conversation is on the
dashboard's "Needs your attention" as a **support** item, and the reminder
email goes out at once.  Answer at owner/support/ ("Customer support"
in the dashboard's shortcuts).

## Watch mode, then answering alone

At first the assistant **drafts** and you send: the customer gets a short
note that a person checks the answers, and the draft waits on the
conversation's page, already in the reply box.  Edit it as you like and
send it; it goes out from you, without the AI label.  The assistant learns
your wording from your edits: your last few edited drafts are shown to it
as examples each time.

Drafts you send unchanged or with small edits (90% of the words the same)
count as approvals.  Once 90% of the last 20 decided drafts in a category
are approvals (`SUPPORT_READY_RATE`, `SUPPORT_READY_MIN_DRAFTS`), the
dashboard says so and the support page offers **Let it answer alone** for
that category.  From then on its answers there go straight to the customer,
labelled "AI assistant".  **Back to watch mode** turns it off again.
"Other" is never answered alone, and only you can switch (agents are
refused).

## What protects customers and the shop

- **Screening before any AI call**: a message that tries to manipulate the
  assistant ("ignore your instructions..."), asks for a person (or an email
  reply that just says "person"), or mentions refunds, damage, health,
  allergies and the like goes to you without the AI seeing it.  So do
  messages past `SUPPORT_AGENT_RUNS_PER_DAY` from one address (floods,
  mail loops).
- **Read-only tools**: order lookup, parcel tracking, catalog search,
  shipping facts.  No address, payment or other customers' orders; refunds
  and cancellations refuse agents in the code.
- **Checks on every answer**: health claims, refund or discount promises,
  outside links, asking for card numbers.  An answer that fails goes to
  you as a draft, never to the customer.
- **Labelled**: the chat says it is an AI above the conversation and on
  each of its messages; its emails start by saying so and offer a person.
- **Spending cap** and **audit log**: see `docs/agents.md`; owner/agents/
  lists every action.
- The AI service failing, or the cap being reached, hands the conversation
  to you; nothing is lost.  A customer message the assistant hasn't dealt
  with after 10 minutes shows on the dashboard.

## Email

Set the support mailbox's IMAP settings to let the assistant read it:

```
SUPPORT_EMAIL=help@yourshop.example   # where customers write; replies come from it
SUPPORT_INBOX=imap
SUPPORT_IMAP_HOST=imap.zoho.com
SUPPORT_IMAP_USER=help@yourshop.example
SUPPORT_IMAP_PASSWORD=...             # an app password, not your login password
# SUPPORT_IMAP_FOLDER=INBOX
# SUPPORT_POLL_MINUTES=2
```

A job (`apps/support/jobs.py`, `poll_inbox`) reads unread emails every few
minutes and marks them read.  Auto-replies, bounces, mailing lists and
mail from the shop's own addresses are skipped.  Replies thread with the
customer's email, and quoted history is dropped.  Replies go out through
`EMAIL_HOST` like order emails, from `SUPPORT_EMAIL`.  Without
`SUPPORT_INBOX` only the chat reaches the assistant, and the support page
says so.

The chat asks for the customer's email so your reply reaches them if they
leave: your chat replies go both to the chat and by email.

## The AI behind it

Until `AGENTS_LIVE=support-agent` and `ANTHROPIC_API_KEY` are set, a
**stand-in** answers: simple rules using the same tools, correct but
wooden, so everything above can be tried on a laptop without an API key.
See `docs/agents.md` for going live, the model, prices and the cap.

## For developers

- `agent.handle(message_id)` (queued by `services.add_customer_message`) does
  the screening, the run and the decision; `services` holds every state
  change (`escalate`, `make_draft`, `agent_answer`, `owner_reply`,
  `discard_draft`, `close`, `readiness`, `set_answers_alone`), each recorded
  as `support.*` in the audit log.
- `tools.py`: the agent's tools; `standin.py`: the stand-in.
- Message bodies are left out of the model-change audit log
  (`AUDIT_EXCLUDED_MODELS`); `support.message_received` and
  `support.email_sent` record each one.
