"""The taxable amount and sales tax each refund gives back.

Refunds issued before this recorded only an amount, not what it was for,
so they are filled in as a share of the order's total, worked out on the
order's refunds to date so a fully refunded order gives back exactly the
tax collected (as the tax reports reckoned them until now)."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from django.db import migrations, models

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def _part(value, numerator, denominator):
    if not denominator:
        return ZERO
    return (value * numerator / denominator).quantize(CENT, rounding=ROUND_HALF_UP)


def fill_in(apps, schema_editor):
    Refund = apps.get_model("fulfillment", "Refund")
    refunded = defaultdict(lambda: ZERO)
    for refund in Refund.objects.select_related("order").order_by("created_at", "pk"):
        order = refund.order
        before = min(refunded[order.pk], order.total)
        refunded[order.pk] += refund.amount
        upto = min(refunded[order.pk], order.total)
        refund.taxable_amount = (_part(upto, order.taxable_amount, order.total)
                                 - _part(before, order.taxable_amount, order.total))
        refund.tax_amount = _part(upto, order.tax_amount, order.total) - _part(before, order.tax_amount, order.total)
        refund.save(update_fields=["taxable_amount", "tax_amount"])


class Migration(migrations.Migration):

    dependencies = [
        ("fulfillment", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="refund",
            name="taxable_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10,
                                      help_text="The part of the order's taxable amount refunded (taxable items "
                                                "and their share of shipping)"),
        ),
        migrations.AddField(
            model_name="refund",
            name="tax_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10,
                                      help_text="The sales tax given back, included in the amount"),
        ),
        migrations.RunPython(fill_in, migrations.RunPython.noop),
    ]
