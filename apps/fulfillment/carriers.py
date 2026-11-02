"""Buying postage, voiding it, and scheduling USPS pickups.

provider() gives the configured one, following checkout's shipping
setting (settings.SHIPPING_PROVIDER):

- EasyPostLabels: EasyPost's API.  With a test key (EZTK...) labels are
  test labels: free, never mailed.  A production key is refused unless
  EASYPOST_ALLOW_LIVE is on (config/settings.py), so real postage is a
  deliberate step.
- FakeLabels: a stand-in for laptops and tests that makes a marked test
  label locally; refused in production.

Errors raise CarrierError with a message for the owner.
"""

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from apps.checkout.shipping import GRAMS_PER_OUNCE, SERVICE_LABELS

from . import labels

log = logging.getLogger(__name__)

# EasyPost's service names by the names customers chose at checkout.
SERVICE_CODES = {label: code for code, label in SERVICE_LABELS.items()}


class CarrierError(Exception):
    """The postage service refused or could not be reached."""


@dataclass
class Purchase:
    shipment_id: str
    tracking_number: str
    service: str
    postage: Decimal
    label: bytes
    label_format: str
    test_mode: bool
    carrier: str = "USPS"


@dataclass
class PickupBooking:
    id: str
    confirmation: str


def service_code(service):
    """EasyPost's name for a service shown as service ("USPS Priority
    Mail"), or service itself if it already is one."""
    return SERVICE_CODES.get(service, service)


def service_choices():
    return [(SERVICE_LABELS.get(code, code), SERVICE_LABELS.get(code, code)) for code in settings.SHIPPING_SERVICES]


def provider():
    if settings.SHIPPING_PROVIDER == "easypost":
        key = settings.EASYPOST_API_KEY
        if not key:
            raise ImproperlyConfigured("SHIPPING_PROVIDER is easypost but EASYPOST_API_KEY is not set")
        if not key.startswith("EZTK") and not settings.EASYPOST_ALLOW_LIVE:
            raise ImproperlyConfigured("Buying real postage needs EASYPOST_ALLOW_LIVE=true")
        return EasyPostLabels(key)
    if settings.PRODUCTION:
        raise ImproperlyConfigured("The stand-in label provider is not for production: set EASYPOST_API_KEY")
    return FakeLabels()


def ounces(grams):
    return float(max((Decimal(grams) / GRAMS_PER_OUNCE).quantize(Decimal("0.1")), Decimal("0.1")))


class FakeLabels:
    """Stand-in labels and pickups: nothing is bought."""

    name = "fake"
    test_mode = True

    def buy(self, order, *, weight_grams, dimensions, service, label_format):
        tracking = "9400" + "".join(secrets.choice("0123456789") for _ in range(18))
        pdf = labels.stand_in_shipping_label_pdf(order, tracking, service, weight_grams)
        return Purchase(f"fake_shp_{tracking[-8:]}", tracking, service, Decimal("0.00"), pdf, "PDF", True)

    def void(self, purchase_shipment_id):
        return "refunded"

    def schedule_pickup(self, day, *, shipment_id, location, instructions, reference):
        code = "".join(secrets.choice("0123456789") for _ in range(8))
        return PickupBooking(f"fake_pickup_{code}", f"WTC{code}")

    def cancel_pickup(self, pickup_id):
        return None


class EasyPostLabels:
    name = "easypost"
    BASE = "https://api.easypost.com/v2"
    TIMEOUT = 30

    def __init__(self, api_key, session=None):
        self.api_key = api_key
        self.session = session or requests.Session()

    @property
    def test_mode(self):
        return self.api_key.startswith("EZTK")

    def _request(self, method, path, payload=None):
        try:
            response = self.session.request(method, f"{self.BASE}{path}", json=payload, auth=(self.api_key, ""),
                                            timeout=self.TIMEOUT)
        except requests.RequestException as exc:
            log.warning("EasyPost %s failed: %s", path, exc)
            raise CarrierError("EasyPost is not answering.  Try again in a minute.") from exc
        try:
            data = response.json()
        except ValueError as exc:
            log.error("EasyPost %s answered something other than JSON: %s", path, response.text[:500])
            raise CarrierError("EasyPost gave an answer that could not be read.  Try again.") from exc
        if response.status_code >= 400:
            message = (data.get("error") or {}).get("message") or f"HTTP {response.status_code}"
            log.error("EasyPost %s refused: %s", path, data)
            raise CarrierError(f"EasyPost refused: {message}")
        return data

    def _download(self, url):
        try:
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            log.error("Could not download the label %s: %s", url, exc)
            raise CarrierError("The label was bought but could not be downloaded.  Open it from EasyPost's "
                               "dashboard, or try printing again.") from exc
        return response.content

    @staticmethod
    def _address(holder):
        data = holder.address.as_dict() if hasattr(holder, "address") else dict(holder)
        return {key: value for key, value in data.items() if value}

    def buy(self, order, *, weight_grams, dimensions, service, label_format):
        parcel = {"weight": ounces(weight_grams)}
        if dimensions:
            parcel.update({"length": float(dimensions[0]), "width": float(dimensions[1]),
                           "height": float(dimensions[2])})
        shipment = self._request("POST", "/shipments", {"shipment": {
            "to_address": self._address(order),
            "from_address": self._address(settings.SHIP_FROM),
            "parcel": parcel,
            "reference": order.number,
            "options": {"label_format": label_format, "label_size": "4x6", "print_custom_1": order.number},
        }})
        code = service_code(service)
        rate = next((r for r in shipment.get("rates") or [] if r.get("carrier") == "USPS" and r.get("service") == code),
                    None)
        if rate is None:
            offered = ", ".join(sorted(SERVICE_LABELS.get(r.get("service"), r.get("service", "?"))
                                       for r in shipment.get("rates") or [] if r.get("carrier") == "USPS"))
            raise CarrierError(f"USPS does not offer {service} for this parcel" +
                               (f"; it offers {offered}." if offered else "."))
        bought = self._request("POST", f"/shipments/{shipment['id']}/buy", {"rate": {"id": rate["id"]}})
        postage_label = bought.get("postage_label") or {}
        url = postage_label.get(f"label_{label_format.lower()}_url") or postage_label.get("label_url")
        if not url:
            raise CarrierError("EasyPost bought the label but sent no file for it.")
        return Purchase(
            shipment_id=bought["id"], tracking_number=bought.get("tracking_code", ""),
            service=SERVICE_LABELS.get(code, service),
            postage=Decimal(str((bought.get("selected_rate") or rate).get("rate", "0"))),
            label=self._download(url), label_format=label_format, test_mode=self.test_mode,
        )

    def void(self, shipment_id):
        """Ask for the postage back (USPS refunds unused labels within 30
        days).  Returns EasyPost's refund status."""
        data = self._request("POST", f"/shipments/{shipment_id}/refund")
        return data.get("refund_status", "submitted")

    def schedule_pickup(self, day, *, shipment_id, location, instructions, reference):
        zone = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.combine(day, time(9)), zone)
        end = timezone.make_aware(datetime.combine(day, time(17)), zone)
        pickup = self._request("POST", "/pickups", {"pickup": {
            "address": self._address(settings.SHIP_FROM),
            "shipment": {"id": shipment_id},
            "min_datetime": start.isoformat(),
            "max_datetime": end.isoformat(),
            "is_account_address": False,
            "instructions": f"{location}. {instructions}".strip(". ") if instructions else location,
            "reference": reference,
        }})
        rates = [r for r in pickup.get("pickup_rates") or [] if r.get("carrier") == "USPS"]
        if not rates:
            raise CarrierError("USPS offered no pickup for that day.  Try another day.")
        booked = self._request("POST", f"/pickups/{pickup['id']}/buy",
                               {"carrier": "USPS", "service": rates[0].get("service", "NextDay")})
        return PickupBooking(booked["id"], booked.get("confirmation", ""))

    def cancel_pickup(self, pickup_id):
        self._request("POST", f"/pickups/{pickup_id}/cancel")
