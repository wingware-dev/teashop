# Marketing (phase 10)

`apps/marketing` keeps the idea backlog, the marketing agent's drafts, the
approval and scheduling calendar, posting to the social networks,
campaigns with their discount codes, and the analytics script.  It builds
on `apps/agents` (docs/agents.md) for the AI and its guardrails, on the
storefront's **Tea notes** articles for the info and history section, and
on the email list (docs/emaillist.md) for emails.

**Nothing is posted, published or sent without your approval** of what,
where and when.  The agent drafts; only you approve, and code refuses
agents whatever their prompt says (`services.approve`,
`publish_article`, `mark_posted`; the email list's own `approve`).

## Your pages

Dashboard → Shortcuts → "Marketing: ideas, posts and calendar"
(`/owner/marketing/`):

- **Marketing**: what to do now (posts to put up by hand, failed posts),
  posts waiting for approval, the idea backlog (add your own, or "Ask the
  assistant for ideas"), what is scheduled for two weeks, unpublished
  articles, and how each network is posted.
- **An idea**: ask the assistant for posts (tick the networks, pick the
  campaign and the time), a tea notes article, or an email for the list;
  or write a post yourself.  Everything made from the idea is listed.
- **A post**: what goes out (the text with its tracked link, the photo,
  the character count), the checks, and Approve / Reject.  Editing an
  approved post takes it off the schedule until you approve it again, so
  approval always covers the version that goes out.
- **Calendar**: the month, with each post at its time and each article on
  the day it appears, coloured by state; on a phone, a list of the days
  that have something.
- **Campaigns**: a name, dates, a description for the assistant, and the
  discount codes that belong to it, with the paid orders and sales those
  codes brought.
- **An article**: as readers will see it, the checks, and Publish from a
  day (today or later; the shop shows it from then).  Edit the text in the
  admin (Storefront → Articles).

The dashboard's "Needs your attention" list has posts waiting for approval
(kind "approvals"; urgent when one is meant to go out within a day),
articles the assistant drafted, each post whose time has come to put up by
hand (kind "posts": a reminder email an hour after its time), and failed
posts (kind "problems").

## The marketing agent

`apps/marketing/agent.py`, named `marketing-agent`.  Its tools are
read-only and never see a customer: the catalog (origin, region, tasting
notes, brewing, whether in stock), the campaigns and their public codes,
and recent posts, ideas and articles (to avoid repeats).  Each task ends
with one final tool: `suggest_ideas`, `save_posts`, `save_article` or
`save_mailing` (or `give_up`, whose reason is shown on the idea).

- **Ideas**: on your request, and once a week by itself (a daily job at
  07:30 runs it when it last suggested a week ago and fewer than 10 ideas
  are new; `MARKETING_WEEKLY_IDEAS=false` stops that).
- **Posts**: one draft per network, at the time you picked, with the
  product's first photo and a link to its page.
- **Articles**: an unpublished draft in Tea notes, linked to its products.
- **Emails**: handed to the email list as a draft (`created_by
  marketing-agent`), where you approve it as any mailing.  One that fails
  the guardrails is held back, as the email list doesn't run them.

It runs on the **stand-in** (`standin.py`): plain rules that use the real
tools and write correct but wooden drafts from the catalog's own facts.
The owner chose to keep the stand-in for now; to try the real model, add
`marketing-agent` to `AGENTS_LIVE` (docs/agents.md).  Its runs count
against the monthly cap like every agent's, and are in the audit log and
on owner/agents/.  Drafting runs on the job queue (`jobs.run_agent`); on a
laptop it runs at once.

## Guardrails

`guardrails.py` checks every post (and article and email) whoever wrote
it; a post with a problem can't be approved until it is fixed.

| Rule | How |
|---|---|
| No health or disease claims | The catalog's copy rules (`apps.catalog.copy_rules`), via `apps.agents.checks` |
| Truthful origin and quality | Protected origins (Darjeeling...) only for certified teas; "organic" only for teas sold as organic and never "certified"; "caffeine-free" only without caffeine |
| No fake reviews or testimonials | The agent's drafts may not have stars, what "customers say" or attributed quotes.  Your own posts get a warning instead: quote only real reviews, word for word, with permission |
| Disclose free products | Tick "shows a free gift" on a post about something we gave a reviewer, influencer or winner: the text must then say so (#gifted, "sent to them free").  A post that talks of influencers, reviewers, giveaways or partnerships without the box is refused |
| No personalised pricing | No "just for you" prices.  A code in a post must be a real, active, public discount code of the post's campaign.  The agent has no customer data |
| Links | Only to the shop (posts store a path; tracking words are added) |
| The network's limits | Length (X counts links as 23), a photo for Instagram and Pinterest, a title for pins, a time |

Refund promises are refused; discounts are allowed only as campaign
codes.  The checks are nets, not a lawyer: read every draft.

## Posting

A job every `MARKETING_SWEEP_MINUTES` (5) looks for approved posts whose
time has come:

- **By hand** (the default for every network): the post goes on your
  dashboard as "Time to post on ...", with the text ready to copy.  Post
  it, then press "I posted it" (with its address if you like).
- **Live**, for networks named in `MARKETING_POST_LIVE` with their
  credentials: each post is its own job, posting through the network's
  API.  If the network is down it tries every 10 minutes for
  `MARKETING_POST_GRACE_HOURS` (6); a refusal (an expired token, say) or a
  timeout, after which it can't know whether the post went up, marks it
  failed for you to check, with "Try again now".  A post more than 6 hours
  late (the worker was stopped) isn't posted in case it is stale.

| Network | Live posting | What you need |
|---|---|---|
| Bluesky | Yes, free | `BLUESKY_HANDLE` and an app password (Bluesky → Settings → Privacy and security → App passwords) in `BLUESKY_APP_PASSWORD` |
| Facebook Page | Yes, free (Meta Graph API) | A Meta app with a Page access token having `pages_manage_posts`: `META_PAGE_ID`, `META_PAGE_TOKEN` |
| Instagram | Yes, free (Meta Graph API) | An Instagram professional account linked to the Page, `instagram_content_publish` on the same token, and `META_INSTAGRAM_ID`.  Instagram fetches the photo from the shop, so the site must be public |
| Pinterest | Yes, free (API v5) | A Pinterest app and an access token with `pins:write` and `boards:read`: `PINTEREST_TOKEN`, `PINTEREST_BOARD_ID` |
| X | No: by hand | X charges for posting through its API |
| TikTok | No: by hand | Needs your video; TikTok lets apps it hasn't audited post only privately |

`manage.py check` refuses a live network without its credentials.  Meta's
and Pinterest's tokens expire (Pinterest's after 30 days unless refreshed;
Meta's long-lived Page tokens can last, but are revoked when a password
changes): an expired token shows as a failed post on the dashboard.  Check
the APIs' current terms and permission reviews before connecting:
publishing permissions need Meta's app review.  `META_GRAPH_VERSION`
(default `v23.0`) picks the Graph API version.

**Buffer** was the other option.  It isn't used: posting through it would
add a subscription and an account with access to every network, and its
public API stopped taking new apps in 2019 (check whether that has changed:
Buffer has talked of a new one).  The networks above with
free APIs are posted directly; the rest by hand.  A Buffer publisher
could be added in `publishers.py` if that changes.

No real social account is connected yet: every network posts by hand
until you set `MARKETING_POST_LIVE`.  Tests mock the APIs.

## Campaigns, codes and analytics

- A campaign's posts carry `utm_source` (the network), `utm_medium=social`,
  `utm_campaign` (the campaign's slug, or `social`) and `utm_content`
  (`post-<id>`) in their links, so the analytics show visits per
  campaign, network and post.
- Its discount codes are ordinary public codes (admin → Discount codes),
  the same for everyone; the campaign's page counts the paid orders that
  used them.  That is how a sale is tied to a campaign, without following
  anyone.
- **Analytics**: `ANALYTICS=plausible` (Plausible's hosted service, from
  about $9 a month: check the price; or self-hosted) or `ANALYTICS=umami` (self-hosted, free),
  with `ANALYTICS_SCRIPT_URL` and `ANALYTICS_SITE_ID` (Plausible: the
  site's domain; Umami: the website id) and optionally
  `ANALYTICS_DASHBOARD_URL` for a link.  Neither sets cookies, so no
  banner is needed; Umami's script is told to respect Do Not Track.  The
  script is added only to the catalog pages (the storefront), never to
  checkout, orders, accounts, the chat, email-list links or owner pages,
  whose addresses can hold something private.  The Content Security
  Policy allows the script's host when it is on, and the privacy policy
  lists it.  Nothing is set up yet.

## Settings

| Setting | Default | What |
|---|---|---|
| `MARKETING_POST_LIVE` | empty | Networks posted through their APIs |
| `BLUESKY_*`, `META_*`, `PINTEREST_*` | empty | Their credentials (above) |
| `MARKETING_POST_AT` | `09:30` | A new post's default local time |
| `MARKETING_SWEEP_MINUTES` | 5 | How often due posts are looked for |
| `MARKETING_POST_GRACE_HOURS` | 6 | How late a live post may still go out |
| `MARKETING_WEEKLY_IDEAS` | true | The agent's weekly ideas |
| `ANALYTICS`, `ANALYTICS_SCRIPT_URL`, `ANALYTICS_SITE_ID`, `ANALYTICS_DASHBOARD_URL` | empty | Analytics (above) |
