"""The monthly spending cap on AI usage, for all agents together.

Before each call the runner asks check(agent, ...) whether the call's
worst-case cost still fits under settings.AGENTS_MONTHLY_CAP (dollars, per
calendar month in the shop's time zone); if not it raises BudgetExceeded and
the agent hands its work to the owner instead.  After the call record()
keeps what it really cost as an AIUsage row.

Prices are settings.AGENTS_PRICE_PER_MTOK: dollars per million input and
output tokens for settings.AGENTS_MODEL.  Check them against Anthropic's
price list when choosing the model.  The stand-ins cost nothing.
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from .ai import STANDIN_MODEL

MILLION = Decimal(1_000_000)
# The dashboard warns from this share of the cap.
WARN_AT = Decimal("0.8")


class BudgetExceeded(Exception):
    """The call would take AI spending past the monthly cap."""


def prices(model):
    """(input, output) dollars per million tokens for model."""
    if model == STANDIN_MODEL:
        return Decimal(0), Decimal(0)
    return settings.AGENTS_PRICE_PER_MTOK


def cost(model, input_tokens, output_tokens):
    price_in, price_out = prices(model)
    total = (Decimal(input_tokens) * price_in + Decimal(output_tokens) * price_out) / MILLION
    return total.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def month_start(now=None):
    local = timezone.localtime(now or timezone.now())
    return timezone.make_aware(datetime(local.year, local.month, 1))


def spent_this_month(now=None, agent=None):
    from .models import AIUsage

    usage = AIUsage.objects.filter(at__gte=month_start(now))
    if agent:
        usage = usage.filter(agent=agent)
    return usage.aggregate(total=Sum("cost"))["total"] or Decimal(0)


def cap():
    return settings.AGENTS_MONTHLY_CAP


def remaining(now=None):
    return max(cap() - spent_this_month(now), Decimal(0))


def check(agent, model, input_tokens, max_output_tokens, now=None):
    """Raise BudgetExceeded unless a call with up to these tokens fits."""
    worst = cost(model, input_tokens, max_output_tokens)
    spent = spent_this_month(now)
    if spent + worst > cap():
        raise BudgetExceeded(
            f"AI spending this month is ${spent:.2f} of the ${cap():.2f} cap; {agent} can't make another call")


def record(agent, reply, purpose=""):
    """Keep what a call cost (an AIUsage row), and return the row."""
    from .models import AIUsage

    return AIUsage.objects.create(
        agent=agent, model=reply.model[:60], live=reply.live, input_tokens=reply.input_tokens,
        output_tokens=reply.output_tokens, cost=cost(reply.model, reply.input_tokens, reply.output_tokens),
        purpose=purpose[:100])
