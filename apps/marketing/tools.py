"""The marketing agent's tools.  All read-only, and none sees customers:
the agent knows the catalog, the campaigns and their public codes, and
what the shop has posted and written, nothing about any person (so it
can't personalise anything).  The tools' inputs come from the model, so
each checks what it is given.

The final tools are how the agent hands over its drafts; agent.py checks
them and saves them as drafts for the owner.
"""

import re
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.agents.runner import Tool, string
from apps.catalog.models import Product
from apps.storefront.browsing import shown_products
from apps.storefront.models import Article

from . import networks
from .models import Campaign, Idea, Post


def _brewing(product):
    if product.kind != Product.Kind.TEA:
        return None
    return {
        "water_temperature_c": product.brew_temp_c,
        "steeping_time": product.brew_minutes or None,
        "grams_per_250ml_cup": str(product.brew_grams) if product.brew_grams else None,
        "infusions": product.brew_infusions,
        "notes": product.brew_notes or None,
    }


def product_facts(product):
    """What the agent may say about a product: the shop's own facts."""
    shop = product.shop_facts() or {}
    # shown_products() annotates from_price over the method of that name.
    price = product.from_price() if callable(product.from_price) else product.from_price
    return {
        "slug": product.slug,
        "name": product.name,
        "what_it_is": product.label_name or product.get_kind_display(),
        "category": product.category.name if product.category_id else None,
        "region": f"{product.region.name}, {product.region.country}" if product.region_id else None,
        "grown_in": shop.get("countries") or None,
        "origin_detail": product.origin_detail or None,
        "protected_origin_certified": product.origin_certified,
        "may_say_organic": product.sold_as_organic,
        "caffeine": product.get_caffeine_display() if product.caffeine else None,
        "summary": product.summary,
        "tasting_notes": product.tasting_notes or None,
        "flavour_notes": [note.name for note in product.flavour_notes.all()],
        "brewing": _brewing(product),
        "from_price": f"${price}" if price is not None else None,
        "in_stock": any(size.packages_available() > 0 for size in product.shop_sizes()),
        "has_photo": product.photos.exists(),
        "page": product.get_absolute_url(),
    }


def search_catalog(query):
    words = [word for word in re.findall(r"[\w'-]+", str(query).lower()) if len(word) >= 3][:8]
    if not words:
        return {"products": [], "note": "Give a tea's name or a few words about it."}
    match = Q()
    for word in words:
        match |= (Q(name__icontains=word) | Q(slug__icontains=word) | Q(summary__icontains=word)
                  | Q(category__name__icontains=word) | Q(region__name__icontains=word))
    products = list(shown_products().filter(match).distinct()[:40])

    def score(product):
        text = " ".join([product.name, product.slug, product.summary,
                         product.category.name if product.category_id else "",
                         product.region.name if product.region_id else ""]).lower()
        return sum(word in product.name.lower() for word in words) * 3 + sum(word in text for word in words)

    products.sort(key=score, reverse=True)
    return {"products": [product_facts(product) for product in products[:3]]}


def list_products():
    new_since = timezone.now() - timedelta(days=45)
    return {"products": [{"slug": p.slug, "name": p.name, "category": p.category.name if p.category_id else None,
                          "region": p.region.name if p.region_id else None, "new": p.created_at >= new_since,
                          "has_photo": bool(p.photos.all())}
                         for p in shown_products().order_by("-featured", "name")[:40]]}


def campaigns():
    today = timezone.localdate()
    found = []
    for campaign in Campaign.objects.exclude(ends_on__lt=today).prefetch_related("codes")[:10]:
        codes = []
        for code in campaign.codes.all():
            if code.problem(subtotal=code.min_subtotal) and "used up" not in code.problem(subtotal=code.min_subtotal):
                continue
            codes.append({"code": code.code, "gives": code.get_kind_display() + (
                f" ({code.value:g}{'%' if code.kind == code.Kind.PERCENT else ' dollars'})"
                if code.kind != code.Kind.FREE_SHIPPING else ""),
                "minimum_order": f"${code.min_subtotal}" if code.min_subtotal else None,
                "last_day": code.ends_on.isoformat() if code.ends_on else None})
        found.append({"name": campaign.name, "about": campaign.description[:500],
                      "starts_on": campaign.starts_on.isoformat() if campaign.starts_on else None,
                      "ends_on": campaign.ends_on.isoformat() if campaign.ends_on else None, "codes": codes})
    return {"campaigns": found, "note": "Codes are public and the same for everyone.  Mention only these codes, "
                                        "and only in posts for their campaign."}


def recent_work():
    return {
        "recent_posts": [{"network": p.network, "when": timezone.localdate(p.scheduled_for).isoformat()
                          if p.scheduled_for else None, "text": p.text[:200]}
                         for p in Post.objects.exclude(status=Post.Status.REJECTED).order_by("-created_at")[:15]],
        "ideas_in_backlog": [idea.title for idea in Idea.objects.filter(status__in=Idea.OPEN)[:30]],
        "tea_notes_articles": [article.title for article in Article.objects.all()[:30]],
        "today": timezone.localdate().isoformat(),
    }


READ_TOOLS = [
    Tool("search_catalog", "The shop's teas and goods matching some words: origin, region, tasting notes, brewing, "
         "caffeine, price, whether in stock, page path.", search_catalog,
         {"query": string("A tea's name or words about it")}, ("query",)),
    Tool("list_products", "Every tea and item in the shop now, briefly.", list_products),
    Tool("campaigns", "The owner's current and coming campaigns and their public discount codes.", campaigns),
    Tool("recent_work", "Recent posts, the ideas in the backlog and the tea notes articles, to avoid repeats; and "
         "today's date.", recent_work),
]

GIVE_UP = Tool("give_up", "Say why you can't do this one; the owner gets the reason.", None,
               {"reason": string("Why, in a short line")}, ("reason",), final=True)

IDEA_ITEM = {"type": "object", "properties": {"title": string("A short title"),
                                             "notes": string("The angle, in a sentence or two"),
                                             "product": string("The product's slug, if about one")},
             "required": ["title", "notes"]}
POST_ITEM = {"type": "object",
             "properties": {"network": string("Which network", enum=list(networks.NETWORKS)),
                            "text": string("The post's text, without the link (it is added)"),
                            "title": string("Pinterest only: the pin's title, up to 100 characters")},
             "required": ["network", "text"]}


def tools_for(task):
    """The tools for one task: "ideas", "posts", "article" or "mailing"."""
    finals = {
        "ideas": Tool("suggest_ideas", "Add your ideas to the owner's backlog (one to five).", None,
                      {"ideas": {"type": "array", "items": IDEA_ITEM, "description": "The ideas"}}, ("ideas",),
                      final=True),
        "posts": Tool("save_posts", "Save one draft per network asked for, for the owner to approve.", None,
                      {"posts": {"type": "array", "items": POST_ITEM, "description": "The drafts"},
                       "link": string("The shop page the posts link to, as a path like /products/assam/, or empty"),
                       "product": string("The slug of the product the photo should come from, or empty")},
                      ("posts",), final=True),
        "article": Tool("save_article", "Save a tea notes article draft for the owner to publish.", None,
                        {"title": string("The title, up to 150 characters"),
                         "summary": string("One sentence for the list of articles, up to 250 characters"),
                         "body": string("Plain-text paragraphs separated by a blank line; '## ' starts a heading"),
                         "products": string("Slugs of the products it is about, comma-separated, or empty")},
                        ("title", "summary", "body"), final=True),
        "mailing": Tool("save_mailing", "Save an email for the list, for the owner to approve.", None,
                        {"subject": string("A subject that says plainly what is inside"),
                         "body": string("Plain text, a blank line between paragraphs")},
                        ("subject", "body"), final=True),
    }
    return READ_TOOLS + [finals[task], GIVE_UP]
