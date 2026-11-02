"""Sales tax on an order.

The rules (New York, where the shop collects; see docs/checkout.md):

- Tea is exempt as food; merchandise and accessories are taxable at the
  combined state and local rate of the delivery address.
- Shipping on an order of tea only is not taxed.  On a mixed order the
  shipping is split in proportion to the items' prices (after discounts),
  and only the taxable items' share is taxed.  This is the safe method the
  plan chose; confirm it with NYS Tax.
- Outside the states in settings.SALES_TAX_STATES nothing is collected
  (sales there are tracked against their thresholds instead: nexus.py).

The split is always computed here.  Only the rate comes from elsewhere:
the owner's table (TaxRate) or Stripe Tax (settings.TAX_PROVIDER).
"""

import logging
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

from .models import CENT, ZERO, TaxRate
from .places import STATE_NAMES

log = logging.getLogger(__name__)

# Stripe's tax code for general tangible goods.
STRIPE_GENERAL_GOODS = "txcd_99999999"


class TaxError(Exception):
    """The rate could not be found; the message is for the customer."""


@dataclass(frozen=True)
class TaxResult:
    rate: Decimal
    taxable_amount: Decimal
    tax: Decimal
    jurisdiction: str
    fallback: bool = False
    calculation_id: str = ""


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def taxable_base(lines, shipping):
    """(taxable items, taxable share of shipping) for lines given as
    [(amount after discount, taxable)]."""
    total = sum((amount for amount, _ in lines), ZERO)
    taxable = sum((amount for amount, is_taxable in lines if is_taxable), ZERO)
    if not shipping or not taxable:
        return money(taxable), ZERO
    if taxable == total:
        return money(taxable), money(shipping)
    return money(taxable), money(shipping * taxable / total)


def calculate(lines, shipping, address):
    """The TaxResult for lines [(amount after discount, taxable)] and the
    shipping charged, delivered to address."""
    state = address.state
    if state not in settings.SALES_TAX_STATES:
        return TaxResult(Decimal("0"), ZERO, ZERO, f"Not collected in {STATE_NAMES.get(state, state)}")
    goods, shipping_share = taxable_base(lines, shipping)
    base = goods + shipping_share
    if not base:
        return TaxResult(Decimal("0"), ZERO, ZERO, "No taxable items")
    if settings.TAX_PROVIDER == "stripe":
        return _stripe_tax(base, address)
    rate, jurisdiction, fallback = table_rate(state, address.zip)
    return TaxResult(rate, base, money(base * rate), jurisdiction, fallback)


def table_rate(state, zip_code):
    """(rate, jurisdiction, used the fallback) from the owner's table."""
    found = TaxRate.lookup(state, zip_code)
    if found:
        return found.rate, found.jurisdiction, False
    fallback = settings.SALES_TAX_FALLBACK_RATES.get(state)
    if fallback is None:
        log.error("No sales tax rate for %s %s and no fallback", state, zip_code)
        raise TaxError("We cannot work out the sales tax for this address yet.  Please write to us.")
    log.warning("No sales tax rate entered for %s %s; charging the fallback rate", state, zip_code)
    return Decimal(fallback), f"{STATE_NAMES.get(state, state)} (highest rate, until the ZIP code's rate is entered)", True


def _stripe_tax(base, address):
    """Ask Stripe Tax for the tax on base at address (the taxable items
    and taxable shipping share as one line of general goods)."""
    import stripe

    from .payments import stripe_client

    try:
        calculation = stripe_client().v1.tax.calculations.create(params={
            "currency": "usd",
            "line_items": [{"amount": int(base * 100), "reference": "taxable", "tax_code": STRIPE_GENERAL_GOODS,
                            "tax_behavior": "exclusive"}],
            "customer_details": {"address_source": "shipping", "address": {
                "line1": address.street1, "line2": address.street2 or None, "city": address.city,
                "state": address.state, "postal_code": address.zip, "country": "US"}},
        })
    except stripe.StripeError as exc:
        log.error("Stripe Tax failed: %s", exc)
        raise TaxError("We could not work out the sales tax just now.  Please try again in a minute.") from exc
    tax = (Decimal(calculation.tax_amount_exclusive) / 100).quantize(CENT)
    rate = (tax / base).quantize(Decimal("0.00001")) if base else Decimal("0")
    return TaxResult(rate, base, tax, f"{STATE_NAMES.get(address.state, address.state)} (Stripe Tax)",
                     calculation_id=calculation.id)
