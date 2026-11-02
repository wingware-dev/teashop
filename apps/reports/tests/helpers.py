"""Orders, lines and refunds for the report tests, with figures fixed by
hand (not through checkout) so each test reads plainly."""

from datetime import datetime
from decimal import Decimal

from django.utils import timezone

from apps.checkout.models import Order, OrderLine
from apps.fulfillment.models import Refund


def at(year, month, day, hour=12):
    return timezone.make_aware(datetime(year, month, day, hour))


def order(when, *, tea="0", goods="0", shipping="0", tax="0", state="NY", discount="0", jurisdiction="",
          rate="0", fee=None, provider="stripe", **fields):
    """A paid order: tea and goods line totals, a discount taken off the
    first line, shipping charged and the tax on the goods (and their share
    of shipping, given as taxable_amount when needed)."""
    tea, goods, shipping, tax, discount = map(Decimal, (tea, goods, shipping, tax, discount))
    fields.setdefault("status", Order.Status.PAID)
    fields.setdefault("taxable_amount", goods if tax else Decimal("0"))
    made = Order.objects.create(
        email="a@example.com", ship_state=state, subtotal=tea + goods, discount_amount=discount,
        shipping_amount=shipping, tax_amount=tax, total=tea + goods - discount + shipping + tax,
        tax_jurisdiction=jurisdiction, tax_rate=Decimal(rate), paid_at=when, payment_provider=provider,
        payment_fee=None if fee is None else Decimal(fee), **fields)
    first = True
    for kind, amount in ((OrderLine.Kind.TEA, tea), (OrderLine.Kind.GOODS, goods)):
        if amount:
            OrderLine.objects.create(order=made, kind=kind, product_name="Assam" if kind == "tea" else "Teapot",
                                     unit_price=amount, quantity=1, line_total=amount,
                                     discount_share=discount if first else Decimal("0"),
                                     taxable=kind == OrderLine.Kind.GOODS)
            first = False
    return made


def refund(made, amount, when, *, taxable="0", tax="0"):
    return Refund.objects.create(order=made, kind=Refund.Kind.PARTIAL, amount=Decimal(amount),
                                 taxable_amount=Decimal(taxable), tax_amount=Decimal(tax), reason="test",
                                 created_at=when)
