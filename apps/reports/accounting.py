"""Each day's sales summary for the accounting package, Wave.

The daily job (jobs.py) works out the day's figures (summary()) and posts
them as one transaction on the Stripe clearing account: the day's item
sales (tea and merchandise apart), shipping charged and sales tax collected,
less refunds and the tax they gave back, less Stripe's fees.  The deposit
is what Stripe should pay out for the day; when the payout reaches the
bank, Wave's bank feed shows it as a transfer from the clearing account.

Inventory bought is not posted: suppliers are paid from the bank or a card,
which Wave's bank feed already brings in, so posting it here would count it
twice.  The day's figures still list it (stock received at landed cost).

client() gives the configured client (settings.WAVE_CLIENT):

- FakeWave: keeps the entry here only, without calling Wave (until the
  shop has a Wave account; also on laptops and in tests).
- WaveAPI: Wave's public GraphQL API, moneyTransactionCreate.  Not yet run
  against a real Wave business: try it on one day first (docs/reports.md).

Each day is posted once (AccountingEntry, and Wave's externalId).  A day
that failed is tried again by the next run.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Sum
from django.utils import timezone

from apps.checkout.models import OrderLine
from apps.inventory.models import Lot

from . import sales
from .models import AccountingEntry

log = logging.getLogger(__name__)
ZERO = Decimal("0.00")

# Lines of the daily transaction: (figure, Wave account key, side), where
# side is the balance change for a positive figure.
LINES = [
    ("tea_sales", "tea_sales", "INCREASE"),
    ("goods_sales", "goods_sales", "INCREASE"),
    ("shipping", "shipping_income", "INCREASE"),
    ("sales_tax", "sales_tax", "INCREASE"),
    ("refunds", "refunds", "DECREASE"),
    ("fees", "payment_fees", "INCREASE"),
]
ACCOUNT_KEYS = ["anchor", "tea_sales", "goods_sales", "shipping_income", "sales_tax", "refunds", "payment_fees"]
# Figures that take money out of the clearing account.
OUTGOING = {"refunds", "fees"}


class AccountingError(Exception):
    pass


@dataclass
class Summary:
    day: date
    orders: int = 0
    tea_sales: Decimal = ZERO  # tea and subscription deliveries, after discounts
    goods_sales: Decimal = ZERO  # merchandise, after discounts
    shipping: Decimal = ZERO
    sales_tax: Decimal = ZERO  # collected, less what refunds gave back
    refunds: Decimal = ZERO  # given back, without its sales tax
    fees: Decimal = ZERO
    fees_estimated: bool = False
    inventory_received: Decimal = ZERO  # for reference: not posted

    @property
    def deposit(self):
        """What the day leaves in the Stripe clearing account."""
        return self.tea_sales + self.goods_sales + self.shipping + self.sales_tax - self.refunds - self.fees

    @property
    def empty(self):
        return not any((self.orders, self.refunds, self.sales_tax, self.fees))

    def as_json(self):
        data = {key: str(value) if isinstance(value, Decimal) else value for key, value in asdict(self).items()}
        data["day"] = self.day.isoformat()
        data["deposit"] = str(self.deposit)
        return data


def summary(day):
    """The Summary of one day (New York time)."""
    end = day + timedelta(days=1)
    result = Summary(day)
    for line in sales._lines(day, end):
        if line.kind == OrderLine.Kind.GOODS:
            result.goods_sales += line.net_amount
        else:
            result.tea_sales += line.net_amount
    for order in sales._orders(day, end):
        result.orders += 1
        result.shipping += order.shipping_amount
        result.sales_tax += order.tax_amount
    refunded, refunded_tax = sales.refunds_total(day, end)
    result.refunds = refunded
    result.sales_tax -= refunded_tax
    _postage, result.fees, result.fees_estimated = sales.fees_and_postage(day, end)
    received = Lot.objects.filter(received_on=day, landed_cost__isnull=False).aggregate(cost=Sum("landed_cost"))
    result.inventory_received = sales.money(received["cost"])
    return result


def transaction_input(result):
    """Wave's MoneyTransactionCreateInput for a Summary."""
    accounts = settings.WAVE_ACCOUNTS
    items = []
    for figure, account, side in LINES:
        amount = getattr(result, figure)
        if not amount:
            continue
        if amount < 0:
            amount, side = -amount, "DECREASE" if side == "INCREASE" else "INCREASE"
        items.append({"accountId": accounts.get(account, f"<{account}>"), "amount": str(amount), "balance": side})
    deposit = result.deposit
    return {
        "businessId": settings.WAVE_BUSINESS_ID or "<business>",
        "externalId": f"{settings.SHOP_NAME.lower().replace(' ', '-')}-daily-{result.day.isoformat()}",
        "date": result.day.isoformat(),
        "description": f"{settings.SHOP_NAME} sales {result.day:%Y-%m-%d}: {result.orders} order"
                       f"{'s' if result.orders != 1 else ''}",
        "anchor": {"accountId": accounts.get("anchor", "<anchor>"), "amount": str(abs(deposit)),
                   "direction": "DEPOSIT" if deposit >= 0 else "WITHDRAWAL"},
        "lineItems": items,
    }


class FakeWave:
    """Keeps the entry here only: nothing is sent."""

    name = "fake"

    def post(self, payload):
        log.info("Stand-in Wave: kept %s (%s)", payload["externalId"], payload["anchor"]["amount"])
        return f"fake-{payload['externalId']}"


MUTATION = """
mutation ($input: MoneyTransactionCreateInput!) {
  moneyTransactionCreate(input: $input) {
    didSucceed
    inputErrors { path message code }
    transaction { id }
  }
}
"""


class WaveAPI:
    """Wave's public GraphQL API.  Needs WAVE_TOKEN, WAVE_BUSINESS_ID and
    every account in WAVE_ACCOUNTS."""

    name = "wave"

    def __init__(self, session=None):
        missing = [key for key in ACCOUNT_KEYS if key not in settings.WAVE_ACCOUNTS]
        if not settings.WAVE_TOKEN or not settings.WAVE_BUSINESS_ID or missing:
            raise ImproperlyConfigured(
                "WAVE_CLIENT is wave but WAVE_TOKEN, WAVE_BUSINESS_ID or WAVE_ACCOUNTS ("
                + ", ".join(missing or ["set"]) + ") is missing")
        self.session = session or requests.Session()

    def post(self, payload):
        try:
            response = self.session.post(
                settings.WAVE_API_URL, timeout=30,
                headers={"Authorization": f"Bearer {settings.WAVE_TOKEN}", "Content-Type": "application/json"},
                data=json.dumps({"query": MUTATION, "variables": {"input": payload}}))
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise AccountingError(f"Wave could not be reached: {exc}") from exc
        if body.get("errors"):
            raise AccountingError("Wave refused it: " + "; ".join(e.get("message", "") for e in body["errors"]))
        result = (body.get("data") or {}).get("moneyTransactionCreate") or {}
        if not result.get("didSucceed"):
            problems = "; ".join(f"{'.'.join(map(str, e.get('path') or []))}: {e.get('message')}"
                                 for e in result.get("inputErrors") or [])
            raise AccountingError(f"Wave refused it: {problems or 'no reason given'}")
        return (result.get("transaction") or {}).get("id", "")


def client():
    return WaveAPI() if settings.WAVE_CLIENT == "wave" else FakeWave()


def post_day(day, wave=None):
    """Post one day's summary, once.  Returns the AccountingEntry.  A day
    already posted (or with nothing to post) is left alone; a failed one is
    tried again.  Raises AccountingError when Wave refuses it, after
    recording why."""
    entry = AccountingEntry.objects.filter(day=day).first()
    if entry and entry.status != AccountingEntry.Status.FAILED:
        return entry
    wave = wave or client()
    result = summary(day)
    entry = entry or AccountingEntry(day=day)
    entry.figures, entry.client, entry.error = result.as_json(), wave.name, ""
    if result.empty:
        entry.status, entry.payload = AccountingEntry.Status.EMPTY, {}
        entry.save()
        return entry
    entry.payload = transaction_input(result)
    try:
        entry.external_id = wave.post(entry.payload)
    except AccountingError as exc:
        entry.status, entry.error = AccountingEntry.Status.FAILED, str(exc)
        entry.save()
        raise
    entry.status, entry.posted_at = AccountingEntry.Status.POSTED, timezone.now()
    entry.save()
    return entry


def days_to_post(today=None):
    """Days up to yesterday not yet posted (or failed), oldest first: from
    WAVE_START_DATE, else from the day after the last entry, else
    yesterday.  At most 60, so a long gap doesn't flood Wave."""
    today = today or timezone.localdate()
    yesterday = today - timedelta(days=1)
    if settings.WAVE_START_DATE:
        first = date.fromisoformat(settings.WAVE_START_DATE)
    else:
        last = AccountingEntry.objects.order_by("-day").first()
        first = last.day + timedelta(days=1) if last else yesterday
    done = set(AccountingEntry.objects.filter(day__gte=first).exclude(status=AccountingEntry.Status.FAILED)
               .values_list("day", flat=True))
    failed = list(AccountingEntry.objects.filter(status=AccountingEntry.Status.FAILED, day__lt=first)
                  .values_list("day", flat=True))
    days = sorted(failed) + [first + timedelta(days=n) for n in range((yesterday - first).days + 1)
                             if first + timedelta(days=n) not in done]
    return days[:60]
