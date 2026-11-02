"""A stand-in for the AI behind the marketing agent: plain rules in place
of the model, so ideas, drafts and the whole approval flow run on a laptop
and in tests without calling an AI service or spending anything.

It answers in the Claude API's shapes (apps.agents.ai) and uses the real
tools: it looks the tea up in the catalog (and the campaigns, for a
campaign's posts), then writes plain, correct drafts from the catalog's
own facts.  They are wooden; the real model writes better ones.
"""

import json
import re
from datetime import date

from apps.agents.ai import STANDIN_MODEL, Reply, estimate_tokens, tool_use_block

from . import networks

LINE_RE = {name: re.compile(rf"^{name}: (.*)$", re.MULTILINE) for name in ("TASK", "NETWORKS", "PRODUCT", "CAMPAIGN")}
IDEA_RE = re.compile(r"IDEA: <untrusted[^>]*>\n(.*?)\n</untrusted", re.DOTALL)
STOP_WORDS = {"about", "post", "posts", "the", "and", "for", "with", "our", "new", "tea", "teas", "write", "some",
              "this", "that", "week", "photo", "photos", "how", "why", "what", "from", "into", "story", "brewing"}
SEASONS = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring", 6: "summer", 7: "summer",
           8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"}


def _prompt(messages):
    return messages[0]["content"][0]["text"]


def _line(prompt, name):
    found = LINE_RE[name].search(prompt)
    return found.group(1).strip() if found else ""


def _results(messages):
    """{tool name: its latest result}."""
    calls, results = {}, {}
    for message in messages:
        for block in message["content"]:
            if block.get("type") == "tool_use":
                calls[block["id"]] = block["name"]
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in calls:
                try:
                    results[calls[block["tool_use_id"]]] = json.loads(block["content"])
                except (TypeError, ValueError):
                    results[calls[block["tool_use_id"]]] = {"error": block.get("content")}
    return results


def _call(name, tool_input=None):
    return [tool_use_block(name, tool_input or {}, block_id=f"toolu_{name}")]


def _give_up(reason):
    return _call("give_up", {"reason": reason})


def _fit(text, limit):
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:.")
    return cut + "…"


def _sentence(text):
    text = " ".join(str(text or "").split())
    return text if not text or text.endswith((".", "!", "?")) else text + "."


def _brew_line(product):
    brewing = product.get("brewing") or {}
    parts = []
    if brewing.get("grams_per_250ml_cup"):
        parts.append(f"{brewing['grams_per_250ml_cup']} g for a 250 ml cup")
    if brewing.get("water_temperature_c"):
        parts.append(f"water at {brewing['water_temperature_c']} °C")
    if brewing.get("steeping_time"):
        parts.append(f"{brewing['steeping_time']}")
    return ("Brew it with " + ", ".join(parts) + ".") if parts else ""


def _tags(product, many=False):
    tags = ["#tea", "#looseleaftea"]
    if product.get("category"):
        tags.append("#" + re.sub(r"\W", "", product["category"].lower()) + "tea")
    if many:
        tags += ["#teatime", "#teashop", "#tealover"]
    return " ".join(dict.fromkeys(tags))


def _where(product):
    if product.get("region"):
        return f"from {product['region']}"
    if product.get("grown_in"):
        return "grown in " + ", ".join(product["grown_in"])
    return ""


def _code_line(results, prompt):
    """The line naming the task's campaign's code, if it has one."""
    name = _line(prompt, "CAMPAIGN").split(" (see the campaigns tool")[0]
    for campaign in (results.get("campaigns") or {}).get("campaigns", []):
        if not name or campaign["name"] != name:
            continue
        for code in campaign.get("codes", []):
            ends = f" until {date.fromisoformat(code['last_day']):%B %-d}" if code.get("last_day") else ""
            return f"Code {code['code']}: {code['gives'].lower()}{ends}."
    return ""


def post_text(network, product, idea_title, code_line=""):
    spec = networks.get(network)
    name, summary = product["name"], _sentence(product.get("summary"))
    where = _where(product)
    tasting = _sentence(product.get("tasting_notes"))
    brew = _brew_line(product)
    head = f"{name}{', ' + where if where else ''}."
    if network in ("x", "bluesky"):
        limit = spec.max_chars - 30
        return _fit(" ".join(filter(None, [head, summary, code_line])), limit)
    if network == "instagram":
        return _fit("\n\n".join(filter(None, [head + " " + summary, tasting, brew, code_line,
                                              "Link in bio.", _tags(product, many=True)])), spec.max_chars)
    if network == "pinterest":
        return _fit(" ".join(filter(None, [summary, tasting, brew])), spec.max_chars)
    if network == "tiktok":
        return _fit(" ".join(filter(None, [head, summary, code_line, _tags(product)])), spec.max_chars)
    return _fit("\n\n".join(filter(None, [head + " " + summary, tasting, brew, code_line])), spec.max_chars)


def _posts(prompt, results):
    found = (results.get("search_catalog") or {}).get("products") or []
    if not found:
        return _give_up("No tea in the catalog matches this idea; name the tea in it")
    product = found[0]
    idea = (IDEA_RE.search(prompt).group(1).splitlines() or [""])[0] if IDEA_RE.search(prompt) else ""
    code_line = _code_line(results, prompt)
    posts = []
    for network in [n for n in _line(prompt, "NETWORKS").split(",") if n in networks.NETWORKS]:
        post = {"network": network, "text": post_text(network, product, idea, code_line)}
        if network == "pinterest":
            post["title"] = _fit(f"{product['name']}: {product.get('what_it_is') or 'loose-leaf tea'}", 100)
        posts.append(post)
    return _call("save_posts", {"posts": posts, "link": product["page"], "product": product["slug"]})


def _article(results):
    found = (results.get("search_catalog") or {}).get("products") or []
    if not found:
        return _give_up("No tea in the catalog matches this idea; name the tea in it")
    product = found[0]
    where = _where(product)
    parts = [_sentence(product.get("summary"))]
    if where or product.get("origin_detail"):
        parts += ["## Where it comes from",
                  _sentence(f"Our {product['name']} comes {where}" if where else product["name"])
                  + (" " + _sentence(product["origin_detail"]) if product.get("origin_detail") else "")]
    if product.get("tasting_notes") or product.get("flavour_notes"):
        parts += ["## In the cup", _sentence(product.get("tasting_notes"))
                  + (" Look for " + ", ".join(product["flavour_notes"]).lower() + "." if product.get("flavour_notes")
                     else "")]
    brew = _brew_line(product)
    if brew:
        notes = _sentence((product.get("brewing") or {}).get("notes"))
        infusions = (product.get("brewing") or {}).get("infusions")
        parts += ["## Brewing it", brew + (f" The leaves give {infusions} good infusions." if infusions else "")
                  + (" " + notes if notes else "")]
    body = "\n\n".join(part.strip() for part in parts if part.strip())
    return _call("save_article", {"title": f"Getting to know {product['name']}",
                                  "summary": _fit(f"Where {product['name']} comes from, how it tastes and how to "
                                                  f"brew it.", 250), "body": body, "products": product["slug"]})


def _mailing(prompt, results):
    found = (results.get("search_catalog") or {}).get("products") or []
    if not found:
        return _give_up("No tea in the catalog matches this idea; name the tea in it")
    product = found[0]
    code_line = _code_line(results, prompt)
    where = _where(product)
    body = "\n\n".join(filter(None, [
        f"This time we'd like you to meet our {product['name']}{', ' + where if where else ''}.",
        _sentence(product.get("summary")) + (" " + _sentence(product.get("tasting_notes"))
                                             if product.get("tasting_notes") else ""),
        _brew_line(product), code_line, f"You'll find it here: {product['page']}"]))
    return _call("save_mailing", {"subject": f"Meet our {product['name']}", "body": body})


def _ideas(results):
    products = (results.get("list_products") or {}).get("products") or []
    work = results.get("recent_work") or {}
    taken = " ".join(work.get("ideas_in_backlog", []) + [p["text"] for p in work.get("recent_posts", [])]
                     + work.get("tea_notes_articles", [])).lower()
    today = date.fromisoformat(work["today"]) if work.get("today") else date.today()
    ideas = []
    fresh = [p for p in products if p["name"].lower() not in taken]
    for product in sorted(fresh, key=lambda p: (not p.get("new"), not p.get("has_photo"), p["name"]))[:3]:
        if product.get("new"):
            ideas.append({"title": f"New in the shop: {product['name']}",
                          "notes": "Introduce it with your photo: where it grows and how it tastes.",
                          "product": product["slug"]})
        else:
            ideas.append({"title": f"How to brew {product['name']}",
                          "notes": "A brewing guide post with your photo, and a tea notes article to link to.",
                          "product": product["slug"]})
    for product in fresh[3:]:
        if product.get("region"):
            ideas.append({"title": f"Where {product['name']} grows: {product['region']}",
                          "notes": "The region, its seasons and how the leaves are made.", "product": product["slug"]})
            break
    season = SEASONS[today.month]
    if f"{season} teas" not in taken:
        ideas.append({"title": f"Teas for {season}", "notes": f"A few of our teas that suit {season} days, with "
                      "brewing tips."})
    return _call("suggest_ideas", {"ideas": ideas[:5]}) if ideas else _give_up("No new ideas: the backlog covers "
                                                                                "every tea")


def _query(prompt):
    product = _line(prompt, "PRODUCT")
    if product:
        return product.replace("-", " ")
    found = IDEA_RE.search(prompt)
    words = [w for w in re.findall(r"[A-Za-z'-]+", found.group(1) if found else "")
             if len(w) >= 3 and w.lower() not in STOP_WORDS]
    return " ".join(words[:6])


def decide(messages):
    prompt = _prompt(messages)
    task = _line(prompt, "TASK")
    results = _results(messages)
    if any(isinstance(r, dict) and r.get("error") for r in results.values()):
        return _give_up("A tool failed")
    if task == "ideas":
        if "list_products" not in results:
            return _call("list_products")
        if "recent_work" not in results:
            return _call("recent_work")
        return _ideas(results)
    if task in ("posts", "article", "mailing"):
        if "search_catalog" not in results:
            query = _query(prompt)
            return _call("search_catalog", {"query": query}) if query else _give_up("The idea names no tea")
        if task != "article" and _line(prompt, "CAMPAIGN") and "campaigns" not in results:
            return _call("campaigns")
        return {"posts": _posts, "mailing": _mailing}[task](prompt, results) if task != "article" \
            else _article(results)
    return _give_up("Unknown task")


class MarketingStandIn:
    model = STANDIN_MODEL

    def complete(self, *, system, messages, tools=(), max_tokens=1024):
        content = decide(messages)
        return Reply(content=content, model=STANDIN_MODEL,
                     input_tokens=estimate_tokens([system, messages, tools]), output_tokens=estimate_tokens(content))
