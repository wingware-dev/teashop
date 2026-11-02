from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def usd(value):
    """12.5 -> "$12.50", -3 -> "−$3.00" (a minus sign, not a hyphen)."""
    if value is None or value == "":
        return ""
    value = Decimal(value)
    return f"−${-value:,.2f}" if value < 0 else f"${value:,.2f}"
