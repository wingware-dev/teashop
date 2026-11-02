"""Shipping: checking addresses and getting live USPS rates.

provider() gives the configured one (settings.SHIPPING_PROVIDER):

- EasyPostShipping: EasyPost's API (https://docs.easypost.com), with a test
  key (EZTK...) until the owner approves live postage.
- FakeShipping: a stand-in with a fixed rate table, for laptops and tests;
  refused in production.

Both answer verify(address) -> Verification and rates(address, grams) ->
[Rate], cheapest first, raising ShippingError when the service fails.
"""

import logging
import math
import re
from dataclasses import dataclass, field, replace
from decimal import Decimal

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .places import ships_to

log = logging.getLogger(__name__)

GRAMS_PER_OUNCE = Decimal("28.349523125")

# What customers see for EasyPost's USPS service names.
SERVICE_LABELS = {
    "GroundAdvantage": "USPS Ground Advantage",
    "Priority": "USPS Priority Mail",
    "Express": "USPS Priority Mail Express",
    "First": "USPS First-Class",
}


class ShippingError(Exception):
    """The shipping service could not answer; the message is for the customer."""


@dataclass(frozen=True)
class Address:
    name: str = ""
    street1: str = ""
    street2: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    phone: str = ""

    def as_dict(self):
        return {"name": self.name, "street1": self.street1, "street2": self.street2, "city": self.city,
                "state": self.state, "zip": self.zip, "phone": self.phone}

    def lines(self):
        return [line for line in (self.name, self.street1, self.street2,
                                  f"{self.city}, {self.state} {self.zip}") if line]

    def same_place(self, other):
        def norm(value):
            return re.sub(r"[^A-Z0-9]", "", (value or "").upper())

        return all(norm(getattr(self, name)) == norm(getattr(other, name))
                   for name in ("street1", "street2", "city", "state")) and self.zip[:5] == other.zip[:5]


@dataclass(frozen=True)
class Rate:
    id: str
    service: str
    amount: Decimal
    days: int = None
    carrier: str = "USPS"
    shipment_id: str = ""

    @property
    def label(self):
        return SERVICE_LABELS.get(self.service, f"{self.carrier} {self.service}")

    @property
    def days_text(self):
        if not self.days:
            return ""
        return "1 day in transit" if self.days == 1 else f"About {self.days} days in transit"


@dataclass
class Verification:
    """The checker's answer: ok (deliverable), the address as the post
    office writes it, and anything to tell the customer."""

    address: Address
    ok: bool
    messages: list = field(default_factory=list)

    def changed_from(self, entered):
        return not self.address.same_place(entered) or self.address.zip != entered.zip


def parcel_grams(size_quantities):
    """Weight of an order: each package's shipping weight, plus the box."""
    return sum(size.shipping_weight() * quantity for size, quantity in size_quantities) + settings.SHIPPING_BOX_GRAMS


def provider():
    if settings.SHIPPING_PROVIDER == "easypost":
        if not settings.EASYPOST_API_KEY:
            raise ImproperlyConfigured("SHIPPING_PROVIDER is easypost but EASYPOST_API_KEY is not set")
        return EasyPostShipping(settings.EASYPOST_API_KEY)
    if settings.PRODUCTION:
        raise ImproperlyConfigured("The stand-in shipping provider is not for production: set EASYPOST_API_KEY")
    return FakeShipping()


def is_configured():
    """Whether checkout can quote shipping here."""
    if settings.SHIPPING_PROVIDER == "easypost":
        return bool(settings.EASYPOST_API_KEY and settings.SHIP_FROM["zip"])
    return not settings.PRODUCTION


class FakeShipping:
    """Stand-in rates: USPS-like prices by weight, no network."""

    name = "fake"
    # (service, base, per started 250 g, days)
    TABLE = [("GroundAdvantage", "5.40", "0.95", 4), ("Priority", "9.85", "1.40", 2), ("Express", "31.40", "2.10", 1)]

    def verify(self, address):
        problem = ships_to(address.state, address.zip)
        if problem:
            return Verification(address, False, [problem])
        if not (address.street1.strip() and address.city.strip()):
            return Verification(address, False, ["Enter the street address and city."])
        tidy = replace(address, street1=address.street1.strip().upper(), street2=address.street2.strip().upper(),
                       city=address.city.strip().upper())
        return Verification(tidy, True, [])

    def rates(self, address, grams):
        steps = max(1, math.ceil(grams / 250))
        services = [row for row in self.TABLE if row[0] in settings.SHIPPING_SERVICES]
        return [Rate(id=f"fake-rate-{service}-{grams}", service=service,
                     amount=(Decimal(base) + Decimal(per) * (steps - 1)).quantize(Decimal("0.01")), days=days,
                     shipment_id=f"fake-shipment-{grams}")
                for service, base, per, days in services]


class EasyPostShipping:
    """EasyPost's REST API (v2), USPS only."""

    name = "easypost"
    BASE = "https://api.easypost.com/v2"
    TIMEOUT = 15

    def __init__(self, api_key, session=None):
        self.api_key = api_key
        self.session = session or requests.Session()

    def _post(self, path, payload):
        try:
            response = self.session.post(f"{self.BASE}{path}", json=payload, auth=(self.api_key, ""),
                                         timeout=self.TIMEOUT)
        except requests.RequestException as exc:
            log.warning("EasyPost %s failed: %s", path, exc)
            raise ShippingError("The shipping service is not answering.  Please try again in a minute.") from exc
        if response.status_code >= 500 or response.status_code in (401, 403, 429):
            log.error("EasyPost %s answered HTTP %s: %s", path, response.status_code, response.text[:500])
            raise ShippingError("The shipping service is not answering.  Please try again in a minute.")
        try:
            return response.status_code, response.json()
        except ValueError as exc:
            log.error("EasyPost %s answered something other than JSON: %s", path, response.text[:500])
            raise ShippingError("The shipping service gave an answer we could not read.  Please try again.") from exc

    @staticmethod
    def _address_payload(address):
        data = address.as_dict()
        return {key: value for key, value in data.items() if value}

    def verify(self, address):
        problem = ships_to(address.state, address.zip)
        if problem:
            return Verification(address, False, [problem])
        status, data = self._post("/addresses", {"address": self._address_payload(address), "verify": ["delivery"]})
        if status >= 400:
            message = (data.get("error") or {}).get("message", "")
            log.warning("EasyPost could not check an address: %s", message)
            return Verification(address, False, ["We could not check this address.  Please look it over."])
        delivery = (data.get("verifications") or {}).get("delivery") or {}
        checked = Address(
            name=address.name, phone=address.phone,
            street1=data.get("street1") or address.street1, street2=data.get("street2") or "",
            city=data.get("city") or address.city, state=data.get("state") or address.state,
            zip=data.get("zip") or address.zip,
        )
        if delivery.get("success"):
            problem = ships_to(checked.state, checked.zip[:5])
            if problem:
                return Verification(checked, False, [problem])
            return Verification(checked, True, [])
        messages = [error.get("message", "") for error in delivery.get("errors") or [] if error.get("message")]
        return Verification(address, False, messages or ["The post office does not know this address."])

    def rates(self, address, grams):
        ship_from = settings.SHIP_FROM
        ounces = (Decimal(grams) / GRAMS_PER_OUNCE).quantize(Decimal("0.1"))
        payload = {"shipment": {
            "to_address": self._address_payload(address),
            "from_address": {key: value for key, value in ship_from.items() if value},
            "parcel": {"weight": float(max(ounces, Decimal("0.1")))},
        }}
        status, data = self._post("/shipments", payload)
        if status >= 400:
            log.error("EasyPost refused a shipment: %s", data)
            raise ShippingError("We could not get shipping prices for this address.  Please check it.")
        rates = []
        for rate in data.get("rates") or []:
            if rate.get("carrier") != "USPS" or rate.get("service") not in settings.SHIPPING_SERVICES:
                continue
            rates.append(Rate(id=rate["id"], service=rate["service"], amount=Decimal(str(rate["rate"])),
                              days=rate.get("delivery_days") or rate.get("est_delivery_days"),
                              shipment_id=data.get("id", "")))
        if not rates:
            messages = [m.get("message", "") for m in data.get("messages") or []]
            log.error("EasyPost gave no USPS rates for a shipment: %s", messages)
            raise ShippingError("We could not get shipping prices for this address.  Please check it.")
        return sorted(rates, key=lambda rate: rate.amount)
