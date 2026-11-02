"""Checks on what an agent wrote, before a customer or the public sees it.

output_problems(text) lists, in plain words, why text must not go out on its
own: health or disease claims (the catalog's copy rules), promises of money
(refunds, credits, discounts, free items) the owner has not approved, links
to sites other than the shop and the carrier, asking for card numbers or
passwords, and text that looks like the agent's own instructions leaking.
Agents send nothing that has a problem; they hand it to the owner instead.
These are nets, not proof: the owner still reads drafts in watch mode.
"""

import re
from urllib.parse import urlsplit

from django.conf import settings

from apps.catalog.copy_rules import health_claims

MONEY_PROMISE_PATTERNS = [
    r"\b(we('| wi)ll|i('| wi)ll|we can|i can|we have|i have|we've|i've)\b.{0,40}\b(refund(ed)?|credit(ed)?|"
    r"reimburs\w*|compensat\w*|waive[ds]?|discount(ed)?)\b",
    r"\b(full|partial) refund\b",
    r"\b(refund|credit) (of|for) \$?\d",
    r"\b(here('| i)s|use) (a |the )?(discount|coupon|promo) code\b",
    r"\b(send|ship) (you )?(a )?(free|replacement|new) (one|order|package|pouch|tin|parcel)\b",
    r"\b(on the house|free of charge|at no (extra )?(cost|charge))\b",
]
_MONEY_RES = [re.compile(pattern, re.IGNORECASE) for pattern in MONEY_PROMISE_PATTERNS]

SECRET_REQUEST_RE = re.compile(
    r"\b(card number|credit card|cvv|cvc|security code|password|social security|ssn|bank account)\b",
    re.IGNORECASE)
LEAK_RE = re.compile(r"<\s*/?\s*untrusted|UNTRUSTED_RULES|\bsk-ant-|\bapi[_ ]key\b|\bsystem prompt\b",
                     re.IGNORECASE)
URL_RE = re.compile(r"\bhttps?://[^\s<>\"')\]]+|\bwww\.[^\s<>\"')\]]+", re.IGNORECASE)

# Hosts besides the shop's own that agents may link to.
ALLOWED_LINK_HOSTS = ("usps.com", "tools.usps.com")


def allowed_hosts():
    hosts = set(ALLOWED_LINK_HOSTS)
    site = urlsplit(settings.SITE_URL).hostname
    if site:
        hosts.add(site.lower())
    return hosts


def _host_allowed(url, hosts):
    host = (urlsplit(url if "://" in url else "https://" + url).hostname or "").lower()
    return any(host == allowed or host.endswith("." + allowed) for allowed in hosts)


def output_problems(text):
    """Why text can't go out without the owner (list of plain-words
    reasons), empty when it may."""
    problems = []
    claims = health_claims(text)
    if claims:
        problems.append("health or disease claim: " + ", ".join(claims))
    if any(pattern.search(text) for pattern in _MONEY_RES):
        problems.append("promises a refund, credit, discount or free item, which only the owner can approve")
    hosts = allowed_hosts()
    links = [url for url in URL_RE.findall(text) if not _host_allowed(url, hosts)]
    if links:
        problems.append("links to another site: " + ", ".join(links[:3]))
    if SECRET_REQUEST_RE.search(text):
        problems.append("mentions card numbers, passwords or other secrets")
    if LEAK_RE.search(text):
        problems.append("looks like it repeats the assistant's own instructions")
    return problems
