"""What an order costs: items, discount, shipping, sales tax and total.

quote() is the one place the figures are worked out, used by the cart
page, the shipping step and the order itself, so the customer sees the
same numbers throughout.  Prices are the catalog's, the same for everyone:
nothing here looks at who the customer is (NY's Algorithmic Pricing
Disclosure Act never applies).
"""

from dataclasses import dataclass, field
from decimal import Decimal

from apps.catalog.models import Product

from . import tax as sales_tax
from .models import CENT, ZERO, CheckoutSettings, DiscountCode


@dataclass
class QuoteLine:
    size: object
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    discount_share: Decimal = ZERO

    @property
    def taxable(self):
        return self.size.product.kind == Product.Kind.GOODS

    @property
    def net(self):
        return self.line_total - self.discount_share


@dataclass
class Quote:
    lines: list
    subtotal: Decimal = ZERO
    discount: DiscountCode = None
    discount_amount: Decimal = ZERO
    discount_problem: str = ""
    free_shipping: bool = False
    free_shipping_over: Decimal = None
    rate: object = None
    shipping_cost: Decimal = ZERO
    shipping_amount: Decimal = ZERO
    tax: sales_tax.TaxResult = None
    messages: list = field(default_factory=list)

    @property
    def items_total(self):
        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self):
        return self.tax.tax if self.tax else ZERO

    @property
    def total(self):
        return self.items_total + self.shipping_amount + self.tax_amount

    @property
    def free_shipping_gap(self):
        """How much more to spend for free shipping (None: no threshold or
        already free)."""
        if self.free_shipping or self.free_shipping_over is None:
            return None
        return max(ZERO, self.free_shipping_over - self.items_total) or None

    @property
    def has_taxable(self):
        return any(line.taxable for line in self.lines)


def allocate(amount, weights):
    """Split amount over weights in proportion, to the cent, the last
    taking what rounding leaves so the parts add up exactly."""
    total = sum(weights, ZERO)
    if not total or not amount:
        return [ZERO for _ in weights]
    parts, left = [], amount
    for index, weight in enumerate(weights):
        if index == len(weights) - 1:
            parts.append(left)
        else:
            part = (amount * weight / total).quantize(CENT)
            parts.append(part)
            left -= part
    return parts


def shipping_price(rate, rates, free):
    """What the customer pays for rate: nothing when shipping is free and
    it is the cheapest service offered."""
    if rate is None:
        return ZERO
    if free and rates and rate.id == min(rates, key=lambda r: r.amount).id:
        return ZERO
    return rate.amount


def quote(items, *, discount=None, email="", rates=None, rate=None, address=None, settings=None):
    """The figures for items [(size option, quantity)].

    discount: a DiscountCode (dropped, with discount_problem set, if it
    can't be used).  rates/rate: the services offered and the one chosen;
    address: where it goes (for tax).  Without rate and address, the quote
    has no shipping or tax yet (the cart page)."""
    settings = settings or CheckoutSettings.current()
    lines = [QuoteLine(size, quantity, size.price, size.price * quantity) for size, quantity in items]
    result = Quote(lines=lines, subtotal=sum((line.line_total for line in lines), ZERO),
                   free_shipping_over=settings.free_shipping_over)
    if discount is not None:
        problem = discount.problem(result.subtotal, email)
        if problem:
            result.discount_problem = problem
        else:
            result.discount = discount
            result.discount_amount = discount.amount_off(result.subtotal)
            for line, share in zip(lines, allocate(result.discount_amount, [line.line_total for line in lines])):
                line.discount_share = share
    result.free_shipping = bool(
        (result.discount and result.discount.kind == DiscountCode.Kind.FREE_SHIPPING)
        or (settings.free_shipping_over is not None and lines and result.items_total >= settings.free_shipping_over)
    )
    if rate is not None:
        result.rate = rate
        result.shipping_cost = rate.amount
        result.shipping_amount = shipping_price(rate, rates or [rate], result.free_shipping)
    if address is not None and rate is not None:
        result.tax = sales_tax.calculate([(line.net, line.taxable) for line in lines], result.shipping_amount,
                                         address)
    return result
