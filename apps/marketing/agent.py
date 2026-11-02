"""The marketing agent: suggests ideas for the backlog, and drafts posts,
tea notes articles and list emails from an idea.  Everything it makes is a
draft the owner approves; it never posts, publishes or sends.

Each task is one apps.agents.runner run with read-only tools (tools.py)
and one final tool that hands over the drafts.  Its output goes through
the marketing guardrails (guardrails.py); a post that fails them is still
saved, marked, so the owner sees it (approval is refused until it is
fixed), and a mailing that fails them is held back, since the email
list's own approval doesn't run these checks.

It runs on the stand-in (standin.py) unless the owner names
"marketing-agent" in AGENTS_LIVE.  The spending cap and audit log come
with the runner.
"""

import logging
import re
from dataclasses import dataclass, field

from django.conf import settings
from django.utils.text import slugify

from apps.agents import ai, budget, runner
from apps.agents.untrusted import clean, wrap
from apps.audit import acting_as_agent, record
from apps.catalog.models import Product

from . import guardrails, networks, services
from .models import Idea
from .standin import MarketingStandIn
from .tools import tools_for

log = logging.getLogger(__name__)

AGENT = "marketing-agent"
MAX_IDEAS = 5

SYSTEM = """\
You are the marketing assistant for {shop}, a small online shop selling loose-leaf tea, weighed and packed by
hand.  You write drafts; the owner, a person, approves or changes every one before anything is posted,
published or sent.

Use only facts from your tools: the shop's catalog, its campaigns and what it has posted.  Rules, always:
- No health or disease claims of any kind (no "detox", "boosts", "heals", "good for your ...", "antioxidants").
  Write about taste, aroma, origin, craft, history and brewing.
- Truthful origin and quality: name a protected origin (Darjeeling and the like) only for a product whose
  protected_origin_certified is true; say "organic" only where may_say_organic is true, never "certified
  organic"; "caffeine-free" only where caffeine is None.  Don't invent facts, awards or numbers.
- Never write reviews, testimonials, star ratings or what customers say or think.
- Never mention gifts to influencers or reviewers, giveaways or partnerships: the owner handles those.
- Prices and codes are the same for everyone: never "just for you" or personal offers.  Mention a discount code
  only if the campaigns tool lists it for this task's campaign.
- Link only to the shop's own pages (paths like /products/...).
Write warmly and plainly, like the owner: short sentences, no hype, few exclamation marks, at most three
hashtags (more on Instagram).  Finish with exactly one call to the task's save tool, or give_up."""

TASKS = {
    "ideas": "Suggest up to {count} new ideas for posts or tea notes articles that aren't already in the backlog or "
             "recently posted.  Think of the season, teas that are new or haven't been posted about, brewing, "
             "origins and history, and current campaigns.",
    "posts": "Write one draft post for each of these networks: {networks}.  Fit each network's length and habits: "
             "{limits}.",
    "article": "Write a tea notes article (300-700 words) for the shop's info and history section.",
    "mailing": "Write a short email for the shop's mailing list (under 250 words).  The list footer (unsubscribe "
               "link, postal address) is added for you.",
}


@dataclass
class Result:
    saved: list = field(default_factory=list)
    problem: str = ""  # why nothing (or not everything) was saved, for the owner

    @property
    def ok(self):
        return bool(self.saved) and not self.problem


def _limits(names):
    parts = []
    for name in names:
        spec = networks.get(name)
        parts.append(f"{spec.label} at most {spec.max_chars - (30 if spec.link_in_text else 0)} characters"
                     + (" (no links in the text)" if not spec.link_in_text else ""))
    return "; ".join(parts)


def build_prompt(task, idea=None, network_names=(), campaign=None):
    lines = [f"TASK: {task}", TASKS[task].format(count=MAX_IDEAS, networks=", ".join(network_names),
                                                 limits=_limits(network_names))]
    if network_names:
        lines.append("NETWORKS: " + ",".join(network_names))
    campaign = campaign or (idea.campaign if idea else None)
    if campaign:
        lines.append(f"CAMPAIGN: {campaign.name} (see the campaigns tool for its codes)")
        if campaign.description:
            lines.append("About the campaign: " + wrap(campaign.description, "owner note", 1000))
    if idea is not None:
        if idea.product_id:
            lines.append(f"PRODUCT: {idea.product.slug}")
        lines.append("IDEA: " + wrap(f"{idea.title}\n{idea.notes}".strip(), "owner note" if not idea.from_agent
                                     else "earlier suggestion", 2000))
    return "\n".join(lines)


def _run(task, purpose, prompt):
    """The outcome, or a Result explaining why there is none."""
    try:
        client = ai.client_for(AGENT, MarketingStandIn)
        outcome = runner.run(AGENT, client, system=SYSTEM.format(shop=settings.SHOP_NAME), prompt=prompt,
                             tools=tools_for(task), purpose=purpose, max_turns=8, max_tokens=2000)
    except budget.BudgetExceeded as exc:
        return None, Result(problem=f"The AI spending cap is reached: {exc}")
    except ai.AIError as exc:
        log.warning("Marketing agent: AI call failed (%s): %s", purpose, exc)
        return None, Result(problem=f"The AI service failed: {exc}"[:300])
    if outcome.final == "give_up":
        return None, Result(problem="The assistant gave up: " + clean(outcome.input["reason"], 250))
    if not outcome.final:
        return None, Result(problem="The assistant could not finish" if outcome.stopped == "turns"
                            else "The assistant answered without saving anything")
    return outcome, None


def _product(slug):
    slug = str(slug or "").strip().lower()
    return Product.objects.filter(slug=slug, is_active=True).first() if slug else None


def _items(value, limit):
    return [item for item in value if isinstance(item, dict)][:limit] if isinstance(value, list) else []


def suggest_ideas():
    """New ideas in the backlog, from the agent."""
    outcome, failed = _run("ideas", "marketing:ideas", build_prompt("ideas"))
    if failed:
        return failed
    result = Result()
    titles = {title.lower() for title in Idea.objects.values_list("title", flat=True)}
    with acting_as_agent(AGENT):
        for item in _items(outcome.input.get("ideas"), MAX_IDEAS):
            title, notes = clean(item.get("title"), 150), clean(item.get("notes"), 1000)
            if not title or title.lower() in titles:
                continue
            problems = guardrails.text_problems(f"{title}\n{notes}", by_agent=True)
            if problems:
                record("marketing.idea_held_back", message=f"{title}: {' '.join(problems)}"[:500])
                continue
            titles.add(title.lower())
            result.saved.append(services.add_idea(title, notes, product=_product(item.get("product")),
                                                  made_by=AGENT))
    if not result.saved:
        result.problem = "The assistant had no new ideas that passed the checks"
    return result


def _link(value, product):
    path = str(value or "").strip()
    site = settings.SITE_URL.rstrip("/")
    if path.startswith(site):
        path = path[len(site):] or "/"
    if not re.fullmatch(r"/[\w\-/]*", path):
        path = ""
    return path or (product.get_absolute_url() if product else "")


def draft_posts(idea, network_names, campaign=None, when=None):
    """One draft post per network for idea, scheduled for when (the next
    default slot if None), waiting for the owner's approval."""
    network_names = [name for name in network_names if name in networks.NETWORKS]
    if not network_names:
        return Result(problem="Choose at least one network")
    campaign = campaign or idea.campaign
    outcome, failed = _run("posts", f"marketing:idea:{idea.pk}",
                           build_prompt("posts", idea, network_names, campaign))
    if failed:
        return failed
    product = _product(outcome.input.get("product")) or idea.product
    photo = product.photos.order_by("sort_order", "pk").first() if product else None
    link = _link(outcome.input.get("link"), product)
    when = when or services.next_slot()
    result, done = Result(), set()
    with acting_as_agent(AGENT):
        for item in _items(outcome.input.get("posts"), len(network_names)):
            network = item.get("network")
            if network not in network_names or network in done:
                continue
            text = clean(item.get("text"), networks.get(network).max_chars + 200)
            if not text:
                continue
            done.add(network)
            result.saved.append(services.new_post(
                network=network, text=text, title=clean(item.get("title"), 100) if network == "pinterest" else "",
                link=link if network != "instagram" else "", photo=photo, product=product,
                campaign=campaign, idea=idea, scheduled_for=when, made_by=AGENT))
        if result.saved and idea.status == Idea.Status.NEW:
            services.set_idea_status(idea, Idea.Status.DRAFTED)
    missing = [networks.get(name).label for name in network_names if name not in done]
    if missing:
        result.problem = "No draft for " + ", ".join(missing)
    return result


def _unique_slug(title):
    from apps.storefront.models import Article

    base = slugify(title)[:150] or "tea-note"
    slug, n = base, 2
    while Article.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def draft_article(idea):
    """A tea notes article draft (unpublished) from idea."""
    from apps.storefront.models import Article

    outcome, failed = _run("article", f"marketing:idea:{idea.pk}", build_prompt("article", idea))
    if failed:
        return failed
    title, summary = clean(outcome.input["title"], 150), clean(outcome.input["summary"], 250)
    body = clean(outcome.input["body"], 12000)
    if not (title and summary and body):
        return Result(problem="The assistant's article was missing its title, summary or text")
    with acting_as_agent(AGENT):
        article = Article.objects.create(title=title, slug=_unique_slug(title), summary=summary, body=body,
                                         written_by=AGENT, is_published=False)
        slugs = [s.strip() for s in str(outcome.input.get("products") or "").split(",") if s.strip()]
        products = list(Product.objects.filter(slug__in=slugs[:6], is_active=True))
        if idea.product_id and idea.product not in products:
            products.append(idea.product)
        article.related_products.set(products)
        idea.articles.add(article)
        if idea.status == Idea.Status.NEW:
            services.set_idea_status(idea, Idea.Status.DRAFTED)
        record("marketing.article_drafted", obj=article, message=title)
    return Result(saved=[article])


def draft_mailing(idea):
    """A list email from idea, handed to the email list as a draft (its own
    approval sends it).  Held back if it fails the guardrails."""
    from apps.emaillist import services as emaillist

    outcome, failed = _run("mailing", f"marketing:idea:{idea.pk}", build_prompt("mailing", idea))
    if failed:
        return failed
    subject, body = clean(outcome.input["subject"], 120), clean(outcome.input["body"], 6000)
    problems = guardrails.text_problems(f"{subject}\n{body}", campaign=idea.campaign, by_agent=True)
    if problems:
        with acting_as_agent(AGENT):
            record("marketing.mailing_held_back", obj=idea, message=" ".join(problems)[:500])
        return Result(problem="The assistant's email was held back: " + " ".join(problems))
    with acting_as_agent(AGENT):
        mailing = emaillist.draft_mailing(subject, body, created_by=AGENT)
        idea.mailings.add(mailing)
        if idea.status == Idea.Status.NEW:
            services.set_idea_status(idea, Idea.Status.DRAFTED)
        record("marketing.mailing_drafted", obj=mailing, message=subject)
    return Result(saved=[mailing])

