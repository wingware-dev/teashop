"""Where the shop ships: the 48 contiguous states and the District of
Columbia.  Alaska, Hawaii, the territories and military (APO/FPO/DPO)
addresses are left out until the shop decides to ship there."""

import re

SHIPPING_STATES = [
    ("AL", "Alabama"), ("AZ", "Arizona"), ("AR", "Arkansas"), ("CA", "California"), ("CO", "Colorado"),
    ("CT", "Connecticut"), ("DE", "Delaware"), ("DC", "District of Columbia"), ("FL", "Florida"),
    ("GA", "Georgia"), ("ID", "Idaho"), ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"),
    ("KY", "Kentucky"), ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"), ("MA", "Massachusetts"),
    ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"), ("MO", "Missouri"), ("MT", "Montana"),
    ("NE", "Nebraska"), ("NV", "Nevada"), ("NH", "New Hampshire"), ("NJ", "New Jersey"), ("NM", "New Mexico"),
    ("NY", "New York"), ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"), ("OK", "Oklahoma"),
    ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"), ("SC", "South Carolina"),
    ("SD", "South Dakota"), ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"), ("VT", "Vermont"),
    ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"), ("WI", "Wisconsin"), ("WY", "Wyoming"),
]
STATE_NAMES = dict(SHIPPING_STATES)

ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")

# ZIP codes that start like this are outside the contiguous states whatever
# state is given: Puerto Rico and the Virgin Islands (006-009), military
# mail (090-098 AE, 340 AA, 962-966 AP), Hawaii and Pacific territories
# (967-969), Alaska (995-999).
EXCLUDED_ZIP_PREFIXES = (
    "006", "007", "008", "009",
    "090", "091", "092", "093", "094", "095", "096", "097", "098",
    "340",
    "962", "963", "964", "965", "966", "967", "968", "969",
    "995", "996", "997", "998", "999",
)


def ships_to(state, zip_code):
    """None if the shop ships to this state and ZIP code, else why not."""
    if state not in STATE_NAMES:
        return "We ship to the 48 contiguous states and DC only, for now."
    if not ZIP_RE.match(zip_code or ""):
        return "Enter a 5-digit ZIP code (or ZIP+4)."
    if zip_code.startswith(EXCLUDED_ZIP_PREFIXES):
        return "We ship to the 48 contiguous states and DC only, for now (no military or territory addresses)."
    return None
