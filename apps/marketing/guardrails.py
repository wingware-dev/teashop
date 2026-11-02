"""The marketing rules every post and article must pass before the owner
can approve it, whoever wrote it (docs/marketing.md, "Guardrails"):

- no health or disease claims (the FDA's warning letters to tea sellers),
  and the shared checks on what agents write (apps.agents.checks): links
  only to the shop, no asking for secrets, no leaked instructions;
- truthful origin and quality: protected origin names (Darjeeling...) only
  for certified teas, "organic" only for teas sold as organic and never
  "certified organic", "caffeine-free" only for teas without caffeine
  (apps.catalog.copy_rules);
- no fake reviews or testimonials: the agent never writes what customers
  "say", star ratings or quotes from reviewers.  The owner may quote a
  real review; their posts get a warning to be sure it is real and that
  they have permission;
- free products given to reviewers, influencers or giveaway winners are
  disclosed (the FTC's endorsement guides): a post marked as showing a
  gift must say so, and one that talks of gifts or partnerships must be
  marked;
- no personalised pricing (New York's Algorithmic Pricing Disclosure
  Act): prices and codes are the same for everyone, so no "just for you"
  prices, and a discount code in a post must be a real, active, public
  code of the post's campaign.  The agent never sees customer data.

problems() lists what blocks approval, warnings() what the owner should
check.  Both are plain sentences.  The rules are nets, not a lawyer: the
owner reads every post before approving it.
"""

import re

from django.utils import timezone

from apps.agents.checks import output_problems
from apps.catalog import copy_rules

from . import networks

TESTIMONIAL_PATTERNS = [
    r"[★⭐]{2,}|\b[1-5](\.\d)?\s*(/\s*5|out of 5|stars?)\b",
    r"\b(customers?|buyers?|shoppers?|reviewers?|people|everyone|fans?|tea lovers)\s+(say|says|said|love|loves|"
    r"rave|raves|agree|swear|tell us)\b",
    r"\btestimonials?\b|\b(rated|reviewed)\s+(by|as)\b|\b(rave|five[- ]star|5[- ]star)\s+reviews?\b",
    r"[\"“][^\"”]{8,}[\"”]\s*[-–—~]\s*[A-Z][a-z]+",
]
_TESTIMONIAL_RES = [re.compile(pattern, re.IGNORECASE) for pattern in TESTIMONIAL_PATTERNS]

DISCLOSURE_RE = re.compile(
    r"#(gifted|ad|sponsored|partner|giveaway)\b|\bgifted\b|\b(sent|gave|given|giving) (them|her|him|you|"
    r"[A-Z@]\w*)?\s*.{0,30}\b(free|at no cost|as a gift)\b|\bfree (sample|tin|pouch|gift)s? (from|courtesy of) us\b|"
    r"\bpaid partnership\b|\bsponsored\b",
    re.IGNORECASE)
GIFT_TALK_RE = re.compile(
    r"\b(influencer|reviewer|ambassador|collab\w*|partnership|sponsor\w*|giveaway|gifted|we sent|sent (them|her|"
    r"him)|#ad)\b", re.IGNORECASE)

PERSONAL_PRICE_RE = re.compile(
    r"\bjust for you\b|\bonly for you\b|\byour (own |personal |special |unique )?(price|discount|deal|rate)\b|"
    r"\bpersonali[sz]ed (price|pricing|discount|offer|deal)s?\b|\bprice(d)? (just )?for you\b|"
    r"\bbecause you (bought|viewed|looked|browsed|ordered)\b|\b(exclusive|special) (price|discount|offer) for you\b",
    re.IGNORECASE)

# "code SPRING10", "use SPRING10", "SPRING10 at checkout"
CODE_RE = re.compile(r"\b(?:code|coupon|promo)\s*:?\s*([A-Z0-9][A-Z0-9-]{2,29})\b|\b([A-Z][A-Z0-9-]{2,29}\d+)\b")

REFUND_PROMISE_RE = re.compile(
    r"\b(full|partial) refunds?\b|\b(refund|credit)s? (of|for) \$?\d|\bmoney[- ]back\b|"
    r"\b(we('| wi)ll|we can|we'd) (refund|credit|reimburse|compensate)\b", re.IGNORECASE)

_MONEY_PROBLEM = "promises a refund, credit, discount or free item"


def _money_problem(problem):
    return problem.startswith(_MONEY_PROBLEM)


def codes_in(text):
    """The discount codes text seems to name (upper case)."""
    found = []
    for match in CODE_RE.finditer(text):
        code = (match.group(1) or match.group(2) or "").upper()
        if code and code not in found:
            found.append(code)
    return found


def _code_problems(text, campaign, day=None):
    from apps.checkout.models import DiscountCode

    problems = []
    named = codes_in(text)
    known = {code.code: code for code in DiscountCode.objects.filter(code__in=named)}
    for code in named:
        found = known.get(code)
        if found is None:
            # A word that only looks like a code ("OOLONG2") is fine unless the text calls it a code.
            if re.search(rf"\b(code|coupon|promo)\s*:?\s*{re.escape(code)}\b", text, re.IGNORECASE):
                problems.append(f"names the discount code {code}, which doesn't exist: create it first (admin → "
                                f"Discount codes) and add it to the campaign")
            continue
        refused = found.problem(subtotal=found.min_subtotal, day=day)
        if refused and "used up" not in refused:
            problems.append(f"names the discount code {code}, which won't work then ({refused})")
        elif campaign is None or not campaign.codes.filter(pk=found.pk).exists():
            problems.append(f"names the discount code {code}, which doesn't belong to this post's campaign; codes go "
                            f"with a campaign, so you can see what each brought")
    return problems


def text_problems(text, *, product=None, campaign=None, gift=False, by_agent=False, day=None):
    """What blocks approval of text (a post, or an article's parts)."""
    problems = []
    for problem in output_problems(text):
        # A discount is fine in marketing, but only as a real public code of the campaign (checked below).
        if not _money_problem(problem):
            problems.append(problem[0].upper() + problem[1:] + ".")
    if REFUND_PROMISE_RE.search(text):
        problems.append("Promises refunds or credits, which only you can decide, one customer at a time.")
    certified = bool(product and product.origin_certified)
    organic = bool(product and product.sold_as_organic)
    problems += copy_rules.origin_problems(text, certified, "The text")
    problems += copy_rules.organic_problems(text, organic, "The text")
    if product is not None:
        from apps.catalog.models import Product

        problems += copy_rules.caffeine_free_problems(text, product.caffeine == Product.Caffeine.NONE, "The text")
    if by_agent and any(pattern.search(text) for pattern in _TESTIMONIAL_RES):
        problems.append("Reads like a review or testimonial (what customers say, stars, a quote).  The assistant "
                        "must never write those: quote only real reviews, yourself.")
    if PERSONAL_PRICE_RE.search(text):
        problems.append("Talks of a price or offer for one person (\"just for you\").  Prices and codes are the same "
                        "for everyone.")
    if gift and not DISCLOSURE_RE.search(text):
        problems.append("Marked as showing a free gift, but doesn't say so.  Add #gifted, or say we sent it to them "
                        "free.")
    if not gift and GIFT_TALK_RE.search(text):
        problems.append("Mentions a reviewer, influencer, giveaway or partnership.  If we gave anyone the product "
                        "free, tick \"shows a free gift\" and say so in the text; if not, reword it.")
    problems += [p[0].upper() + p[1:] + "." for p in _code_problems(text, campaign, day)]
    return problems


def problems(post):
    """What blocks the post's approval."""
    spec = networks.get(post.network)
    found = text_problems(" ".join(filter(None, [post.title, post.text])), product=post.product,
                          campaign=post.campaign, gift=post.gift, by_agent=post.from_agent and not post.edited_by_owner,
                          day=timezone.localdate(post.scheduled_for) if post.scheduled_for else None)
    if not post.text.strip():
        found.append("It has no text.")
    if post.length() > spec.max_chars:
        found.append(f"It is {post.length()} characters; {spec.label} allows {spec.max_chars}.")
    if spec.needs_image and not post.photo_id:
        found.append(f"{spec.label} needs a photo: pick one of your product photos.")
    if post.network == "pinterest" and not post.title.strip():
        found.append("A pin needs a title.")
    if post.scheduled_for is None:
        found.append("It has no date and time to go out.")
    return found


def warnings(post):
    """What the owner should check; doesn't block approval."""
    found = []
    text = " ".join(filter(None, [post.title, post.text]))
    if not post.from_agent or post.edited_by_owner:
        if any(pattern.search(text) for pattern in _TESTIMONIAL_RES):
            found.append("Quotes or sums up what customers say.  Use only real reviews, word for word, with the "
                         "writer's permission, and never hide bad ones.")
    if post.spec.needs_video:
        found.append("TikTok needs your video; this is its caption.")
    if post.network == "instagram" and "http" in post.text:
        found.append("Links in Instagram captions aren't clickable.")
    return found


def article_problems(title, summary, body, by_agent=False):
    """What blocks publishing a tea notes article (the storefront's own
    health-claim check runs too)."""
    return text_problems("\n".join([title, summary, body]), by_agent=by_agent)
