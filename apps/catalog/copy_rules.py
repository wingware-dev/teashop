"""Rules for words customers see: product names and copy, section intros,
tea info articles and AI-made page variants.

- No health or disease claims.  Tea is food: saying it cures, treats,
  prevents or heals anything makes it an unapproved drug in the FDA's
  eyes, and herbal tea copy is where its warning letters most often land.
  The list below catches the usual wording; it is a net, not a lawyer, so
  copy still gets a human read before it goes live.
- A herbal product's name says "herbal tea" or "tisane", since it is not
  from the tea plant.
- "Caffeine-free" only for a product whose caffeine level is None.
- Protected origin names (Darjeeling and the like) only for a product
  marked as certified genuine, with the certificate kept on the lot.
- "Organic" only for a product marked as sold as organic, and never as
  "certified organic", "USDA organic" or a seal: the shop repacks under
  the USDA exemption for handlers with under $5,000 a year of organic
  sales, which allows the plain word but not a claim to be certified.

Each check returns a list of problems in plain words, empty when the text
passes, so forms, the admin and the AI variant importer can all show them.
"""

import re

from django.conf import settings

# (pattern, kind of claim to tell the writer).  Word boundaries keep "heal"
# from matching "health"; claims about health are caught by the phrases
# that make them claims ("supports healthy ...", "boosts immunity").
HEALTH_CLAIM_PATTERNS = [
    (r"\bcur(e|es|ed|ing|ative)\b", "cure"),
    # "A lovely treat" is fine; "treats colds" or "to treat" is not.
    (r"\b(treats|treated|treating|treatments?|to treat)\b(?!\s+(yourself|yourselves|someone|a friend|friends|guests))",
     "treat (as a remedy)"),
    (r"\bprevent(s|ed|ing|ion|ive)?\b", "prevent"),
    (r"\bheal(s|ed|ing|er)?\b", "heal"),
    (r"\bremed(y|ies|ial)\b", "remedy"),
    (r"\bmedicin(e|es|al)\b", "medicinal"),
    (r"\btherapeutic\b|\btherapy\b", "therapeutic"),
    (r"\bclinical(ly)?\b", "clinically"),
    # "Palate-cleansing" describes taste, so it passes.
    (r"\bdetox(ify|ifying|ification|es)?\b|(?<!palate[- ])\bcleans(e|es|ing)\b", "detox or cleanse"),
    (r"\bimmun(e|ity)\b", "immunity"),
    (r"\bboost(s|ing)?\s+(your\s+)?(metabolism|energy|immun\w*|health|mood)\b", "boosts a body function"),
    (r"\bmetabolism\b", "metabolism"),
    (r"\bweight[- ]loss\b|\blose weight\b|\bfat[- ]burn\w*\b|\bslimming\b", "weight loss"),
    (r"\banti[- ]?(inflammatory|oxidants?|cancer|aging|ageing|bacterial|viral|anxiety)\b", "anti-..."),
    (r"\bantioxidants?\b", "antioxidants"),
    (r"\b(cancer|tumou?rs?|diabet\w*|arthritis|alzheimer\w*|dementia|asthma|infections?)\b", "a disease"),
    (r"\b(blood pressure|blood sugar|cholesterol|heart disease|hypertension)\b", "blood pressure, sugar or cholesterol"),
    (r"\b(anxiety|depression|insomnia|migraines?|headaches?|nausea|indigestion|bloating|constipation)\b",
     "a condition or symptom"),
    # Not "cold": cold-brewed tea is fine.
    (r"\b(colds|common cold|flu|sore throats?|coughs?|congestion)\b", "colds, flu or sore throats"),
    (r"\b(relie(f|ve|ves|ving))\b", "relief"),
    (r"\b(aids?|helps?|supports?|promotes?)\s+(digestion|sleep|relaxation|recovery|circulation|focus|"
     r"weight|the immune|immun\w*|healthy)\b", "aids digestion, sleep, focus..."),
    (r"\bsleep aid\b|\bhelps? you sleep\b", "sleep aid"),
    (r"\b(superfood|wellness shot)\b", "superfood"),
]
_HEALTH_RES = [(re.compile(pattern, re.IGNORECASE), label) for pattern, label in HEALTH_CLAIM_PATTERNS]

HERBAL_NAME_RE = re.compile(r"\b(herbal tea|herbal infusion|tisane)s?\b", re.IGNORECASE)
CAFFEINE_FREE_RE = re.compile(r"\b(caffeine[- ]free|decaf(feinated)?|no caffeine|zero caffeine)\b", re.IGNORECASE)
ORGANIC_RE = re.compile(r"\borganic(ally)?\b", re.IGNORECASE)
# What an exempt (uncertified) handler may not say: that the product or the
# shop is certified, or anything that stands for the USDA seal.
CERTIFIED_ORGANIC_RE = re.compile(
    r"\bcertified[- ]organic\b|\borganic(ally)?[- ]certified\b|\bcertified (as |100% |100 percent )?organic\b"
    r"|\bUSDA\b|\borganic seal\b",
    re.IGNORECASE,
)


def health_claims(text):
    """The health or disease claim wordings found in text, each as
    '"the words" (kind of claim)', in the order they appear."""
    if not text:
        return []
    matches = []
    for order, (regex, label) in enumerate(_HEALTH_RES):
        for match in regex.finditer(text):
            matches.append((match.start(), -match.end(), order, match.group(0), label))
    # Longest match first at each start, so a match that falls inside one
    # already reported ("immunity" in "boosts immunity") is dropped rather
    # than warned about twice.
    found = []
    reported_end = -1
    for start, neg_end, _, words, label in sorted(matches):
        if -neg_end <= reported_end:
            continue
        found.append(f'"{words}" ({label})')
        reported_end = -neg_end
    return found


def health_claim_problems(text, where="This text"):
    claims = health_claims(text)
    if not claims:
        return []
    return [
        f"{where} reads as a health or disease claim: {', '.join(claims)}.  Describe taste, aroma, origin "
        "and how to brew it instead."
    ]


def protected_origins():
    """The protected origin names (lowercase -> as written), from the
    CATALOG_PROTECTED_ORIGINS setting."""
    return {name.lower(): name for name in settings.CATALOG_PROTECTED_ORIGINS}


def protected_origins_in(text):
    """Protected origin names that text uses, as configured."""
    if not text:
        return []
    found = []
    for lower, name in protected_origins().items():
        if re.search(r"\b" + re.escape(lower) + r"\b", text, re.IGNORECASE):
            found.append(name)
    return found


def herbal_name_problems(name):
    if name and not HERBAL_NAME_RE.search(name):
        return [f'"{name}" is a herbal product: put "herbal tea" or "tisane" in its name, e.g. "{name} herbal tea".']
    return []


def caffeine_free_problems(text, caffeine_is_none, where="This text"):
    match = CAFFEINE_FREE_RE.search(text or "")
    if match and not caffeine_is_none:
        return [f'{where} says "{match.group(0)}", but the caffeine level is not set to None.']
    return []


def origin_problems(text, certified, where="This text"):
    names = protected_origins_in(text)
    if names and not certified:
        return [
            f"{where} uses the protected origin name {', '.join(names)}.  Use it only for certified genuine tea: "
            'tick "Origin certified" and keep the certificate with the lot, or describe it another way.'
        ]
    return []


def organic_problems(text, sold_as_organic, where="This text"):
    """'Organic' only for a product sold as organic, and never in a form
    that claims certification or the USDA seal."""
    problems = []
    certified = CERTIFIED_ORGANIC_RE.search(text or "")
    if certified:
        problems.append(
            f'{where} says "{certified.group(0)}".  The shop is not certified organic (it sells under the USDA '
            'small-business exemption), so it may say "organic" but not "certified organic", "USDA" or the seal.'
        )
    organic = ORGANIC_RE.search(text or "")
    if organic and not sold_as_organic:
        problems.append(f'{where} says "{organic.group(0)}", but the product is not marked as sold as organic.')
    return problems
