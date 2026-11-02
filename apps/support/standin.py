"""A stand-in for the AI behind the support agent: simple rules in place of
the model, so the whole flow (tools, drafts, escalations, the chat) runs on
a laptop and in tests without calling an AI service or spending anything.

It answers in the same shapes as the Claude API (apps.agents.ai): it reads
the customer's latest message, calls one tool (order lookup, catalog or
shipping), then replies from the tool's result, or escalates.  Its replies
are plain and correct but wooden; the real model writes better ones in the
owner's voice.
"""

import json
import re

from apps.agents.ai import STANDIN_MODEL, Reply, estimate_tokens, tool_use_block

from .tools import ORDER_NUMBER_RE

LATEST_RE = re.compile(r"LATEST MESSAGE:\s*<untrusted[^>]*>\n(.*?)\n</untrusted", re.DOTALL)

ORDER_WORDS = re.compile(r"\b(order|track\w*|where('s| is)|status|shipped|dispatched|arriv\w*|deliver\w*|parcel|"
                         r"package)\b", re.IGNORECASE)
BREWING_WORDS = re.compile(r"\b(brew\w*|steep\w*|infus\w*|temperature|degrees|how (much|many grams)|water|"
                           r"cold[- ]brew|iced|teapot|gongfu|caffeine)\b", re.IGNORECASE)
SHIPPING_WORDS = re.compile(r"\b(ship\w*|deliver\w*|postage|usps|how long|how soon|free shipping|arrive|transit)\b",
                            re.IGNORECASE)
STOP_WORDS = {"how", "the", "should", "brew", "brewing", "steep", "steeping", "long", "what", "temperature", "water",
              "your", "you", "for", "and", "much", "many", "grams", "tea", "teas", "can", "does", "with", "this",
              "that", "best", "way", "make", "hello", "thanks", "please", "would", "like", "know", "want", "cup",
              "minutes", "hot", "iced", "cold", "infusions", "infuse", "caffeine", "there", "any", "have"}


def _latest(messages):
    first = messages[0]["content"][0]["text"]
    found = LATEST_RE.findall(first)
    return found[-1] if found else ""


def _results(messages):
    """[(tool name, input, result dict)] so far."""
    calls, results = {}, []
    for message in messages:
        for block in message["content"]:
            if block.get("type") == "tool_use":
                calls[block["id"]] = block
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in calls:
                call = calls[block["tool_use_id"]]
                try:
                    value = json.loads(block["content"])
                except (TypeError, ValueError):
                    value = {"error": block.get("content")}
                results.append((call["name"], call["input"], value))
    return results


def _escalate(reason):
    return [tool_use_block("escalate", {"reason": reason})]


def _reply(category, text):
    return [tool_use_block("reply", {"category": category, "text": text})]


def _order_reply(result):
    lines = [f"Your order {result['number']} is: {result['status'].lower()}."]
    if result.get("shipped_on"):
        lines.append(f"It shipped on {result['shipped_on']}" + (f" by {result['shipping_service']}"
                                                                if result.get("shipping_service") else "") + ".")
        if result.get("tracking_link"):
            lines.append(f"You can follow it here: {result['tracking_link']}")
    elif result.get("promised_to_ship_by"):
        lines.append(f"We promise to ship it by {result['promised_to_ship_by']}, and we'll email you the tracking "
                     "number when it leaves.")
    return "\n".join(lines)


def _brewing_reply(product):
    brewing = product.get("brewing") or {}
    parts = []
    if brewing.get("grams_per_250ml_cup"):
        parts.append(f"use about {brewing['grams_per_250ml_cup']} g of leaves for a 250 ml (8 oz) cup")
    if brewing.get("water_temperature"):
        parts.append(f"with water at {brewing['water_temperature']}")
    if brewing.get("steeping_time"):
        parts.append(f"and steep for {brewing['steeping_time']}")
    text = f"For our {product['name']}, " + " ".join(parts) + "."
    if brewing.get("infusions"):
        text += f"  The leaves are good for {brewing['infusions']} infusions."
    if brewing.get("notes"):
        text += f"  {brewing['notes']}"
    return text


def _shipping_reply(info):
    if info.get("away_now"):
        return None  # vacations have exceptions worth a person's answer
    transit = info["usual_time_in_transit_after_shipping"]
    text = (f"We weigh and pack each order by hand and ship within {info['ships_within']}.  After that, USPS "
            f"Ground Advantage usually takes {transit['USPS Ground Advantage']} and Priority Mail "
            f"{transit['USPS Priority Mail']}.  We email you the tracking number when it ships.")
    if info.get("free_shipping_from"):
        text += f"  Orders of {info['free_shipping_from']} or more ship free."
    return text


def decide(messages):
    """The blocks the stand-in answers with."""
    text = _latest(messages)
    results = _results(messages)
    number = ORDER_NUMBER_RE.search(text)
    if results:
        name, _, result = results[-1]
        if result.get("error"):
            return _escalate("A tool failed")
        if name == "lookup_order":
            if not result.get("found"):
                return _escalate("Order number not found for this customer's email")
            return _reply("order_status", _order_reply(result))
        if name == "search_catalog":
            products = [p for p in result.get("products", []) if p.get("brewing")]
            if not products or not any(products[0]["brewing"].values()):
                return _escalate("No brewing facts found for the tea asked about")
            return _reply("brewing", _brewing_reply(products[0]))
        if name == "shipping_info":
            reply = _shipping_reply(result)
            return _reply("shipping", reply) if reply else _escalate("The shop is away: shipping dates need a person")
        return _escalate("Not sure how to answer")
    if number:
        return [tool_use_block("lookup_order", {"order_number": number.group(0).upper()})]
    if BREWING_WORDS.search(text):
        words = [w for w in re.findall(r"[A-Za-z'-]+", text) if len(w) >= 3 and w.lower() not in STOP_WORDS]
        if not words:
            return _escalate("A brewing question without a tea named")
        return [tool_use_block("search_catalog", {"query": " ".join(words[:6])})]
    if ORDER_WORDS.search(text) and re.search(r"\b(my|our)\s+(order|parcel|package|tea)\b", text, re.IGNORECASE):
        return _reply("order_status", "I can look that up for you.  What is your order number?  It is in your "
                      "order confirmation email and looks like 261101-AB2C.")
    if SHIPPING_WORDS.search(text):
        return [tool_use_block("shipping_info", {})]
    return _escalate("Not a question the assistant can answer for sure")


class SupportStandIn:
    model = STANDIN_MODEL

    def complete(self, *, system, messages, tools=(), max_tokens=1024):
        content = decide(messages)
        return Reply(content=content, model=STANDIN_MODEL,
                     input_tokens=estimate_tokens([system, messages, tools]), output_tokens=estimate_tokens(content))
