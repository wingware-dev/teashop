"""Figures for the New York sales tax return and for quarterly estimated
income tax (a sole proprietor: Schedule C profit, self-employment tax,
federal Form 1040-ES and New York IT-2105).

These are the shop's own figures to file from; they don't replace the
forms' instructions or a tax preparer.  New York's sales tax quarters run
March to May, June to August, September to November and December to
February, each due on the 20th of the month after; an annual filer's year
runs March to February.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from apps.checkout.models import Order
from apps.checkout.nexus import TOOK_PAYMENT, refund_shares

from . import sales

ZERO = Decimal("0.00")
money = sales.money
aware = sales.aware


# -- New York sales tax --------------------------------------------------------

@dataclass(frozen=True)
class Period:
    start: date
    end: date  # the day after the last
    label: str
    due: date

    @property
    def last_day(self):
        return self.end - timedelta(days=1)


def _add_months(day, months):
    return sales.purchasing.add_months(day, months)


def ny_quarter(day):
    """The New York sales tax quarter (Mar-May, Jun-Aug, Sep-Nov, Dec-Feb)
    holding day."""
    month = day.month
    start_month = 12 if month in (12, 1, 2) else (month - 3) // 3 * 3 + 3
    year = day.year - 1 if month in (1, 2) else day.year
    start = date(year, start_month, 1)
    end = _add_months(start, 3)
    last = end - timedelta(days=1)
    return Period(start, end, f"{start:%b %Y} to {last:%b %Y}", end.replace(day=20))


def ny_quarters(today=None, count=6):
    """The last `count` New York sales tax quarters to today, newest first."""
    today = today or timezone.localdate()
    periods, day = [], today
    for _ in range(count):
        period = ny_quarter(day)
        periods.append(period)
        day = period.start - timedelta(days=1)
    return periods


@dataclass
class Jurisdiction:
    name: str
    rate: Decimal
    taxable: Decimal = ZERO
    tax: Decimal = ZERO

    @property
    def rate_percent(self):
        return (self.rate * 100).quantize(Decimal("0.001")).normalize()


@dataclass
class SalesTaxReturn:
    period: Period
    orders: int = 0
    gross: Decimal = ZERO  # sales delivered in New York, without the tax
    taxable: Decimal = ZERO
    tax: Decimal = ZERO
    refunds: int = 0
    refunded: Decimal = ZERO  # without its tax, already taken off gross
    refunded_tax: Decimal = ZERO  # already taken off tax
    outside: Decimal = ZERO  # sales delivered outside New York
    jurisdictions: list = field(default_factory=list)

    @property
    def nontaxable(self):
        return self.gross - self.taxable


def ny_sales_tax(period):
    """The SalesTaxReturn for a period: New York deliveries paid in it,
    less the refunds issued in it, by the jurisdiction and rate charged."""
    result = SalesTaxReturn(period)
    paid = Order.objects.filter(TOOK_PAYMENT, paid_at__gte=aware(period.start), paid_at__lt=aware(period.end))
    places = {}

    def place(order):
        key = (order.tax_jurisdiction or "No tax charged", order.tax_rate)
        return places.setdefault(key, Jurisdiction(*key))

    for order in paid.filter(ship_state="NY"):
        result.orders += 1
        result.gross += order.total - order.tax_amount
        result.taxable += order.taxable_amount
        result.tax += order.tax_amount
        spot = place(order)
        spot.taxable += order.taxable_amount
        spot.tax += order.tax_amount
    outside = paid.exclude(ship_state="NY").aggregate(sales=Sum("total"), tax=Sum("tax_amount"))
    result.outside = (outside["sales"] or ZERO) - (outside["tax"] or ZERO)
    for share in refund_shares(created_at__gte=aware(period.start), created_at__lt=aware(period.end)):
        order = share.refund.order
        if order.ship_state != "NY":
            result.outside -= share.amount - share.tax
            continue
        result.refunds += 1
        result.refunded += share.amount - share.tax
        result.refunded_tax += share.tax
        result.gross -= share.amount - share.tax
        result.taxable -= share.taxable
        result.tax -= share.tax
        spot = place(order)
        spot.taxable -= share.taxable
        spot.tax -= share.tax
    result.jurisdictions = sorted((j for j in places.values() if j.taxable or j.tax),
                                  key=lambda j: (-j.tax, j.name))
    return result


# -- Quarterly estimated income tax ---------------------------------------------

SE_EARNINGS_SHARE = Decimal("0.9235")
SOCIAL_SECURITY_RATE = Decimal("0.124")
MEDICARE_RATE = Decimal("0.029")


def estimate_periods(year):
    """The four estimated-tax periods of a year and their due dates (federal
    and New York use the same).  A due date on a weekend or holiday moves
    to the next working day; check the form."""
    return [
        Period(date(year, 1, 1), date(year, 4, 1), "January to March", date(year, 4, 15)),
        Period(date(year, 4, 1), date(year, 6, 1), "April and May", date(year, 6, 15)),
        Period(date(year, 6, 1), date(year, 9, 1), "June to August", date(year, 9, 15)),
        Period(date(year, 9, 1), date(year + 1, 1, 1), "September to December", date(year + 1, 1, 15)),
    ]


def self_employment_tax(profit):
    earnings = max(profit, ZERO) * SE_EARNINGS_SHARE
    social = min(earnings, settings.SOCIAL_SECURITY_WAGE_BASE) * SOCIAL_SECURITY_RATE
    return money(social + earnings * MEDICARE_RATE)


@dataclass
class Estimate:
    period: Period
    profit: Decimal  # in this period
    to_date: Decimal  # since January 1, through the period's end
    se_tax: Decimal  # self-employment tax on the profit to date
    federal: Decimal  # income tax set-aside on it
    state: Decimal
    payment: Decimal  # the part of the year's estimate that falls in this period
    started: bool  # the period has begun

    @property
    def total_to_date(self):
        return self.se_tax + self.federal + self.state


def profit(start, end):
    """The shop's profit from start up to end as far as this app knows it:
    net sales less cost of goods, postage, payment fees, loss and samples.
    Other expenses (hosting, supplies, home office) are in Wave."""
    figures = sales.margin(start, end)
    return money(figures.after_fulfilment - figures.loss - figures.samples)


def estimated_tax(year, today=None):
    """[Estimate] for each period of year: the profit to date, the
    self-employment tax and income tax set-aside on it, and what to pay
    for the period (the estimate to date less the earlier periods')."""
    today = today or timezone.localdate()
    rows, earlier, to_date = [], ZERO, ZERO
    for period in estimate_periods(year):
        started = period.start <= today
        period_profit = profit(period.start, min(period.end, today + timedelta(days=1))) if started else ZERO
        to_date += period_profit
        se_tax = self_employment_tax(to_date)
        income = max(to_date - se_tax / 2, ZERO)
        federal = money(income * settings.ESTIMATED_TAX_FEDERAL_RATE)
        state = money(income * settings.ESTIMATED_TAX_STATE_RATE)
        total = se_tax + federal + state
        rows.append(Estimate(period, period_profit, to_date, se_tax, federal, state,
                             max(total - earlier, ZERO), started))
        earlier = max(earlier, total)
    return rows
