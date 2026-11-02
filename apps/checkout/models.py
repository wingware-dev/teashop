"""Carts, orders, discount codes, sales tax rates and thresholds, customer
accounts and subscriptions.

Money is in US dollars as Decimal with two places.  An order's figures are
fixed when the customer goes to pay, from pricing.quote(), and never
recalculated afterwards: what the customer agreed to is what is kept.
"""

import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import SizeOption

from .places import SHIPPING_STATES, STATE_NAMES

ZERO = Decimal("0.00")
CENT = Decimal("0.01")

# Readable order numbers: no 0/O, 1/I/L to confuse on the phone.
_NUMBER_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_token():
    return secrets.token_urlsafe(24)


def add_business_days(day, days):
    """day plus this many working days (Monday to Friday)."""
    while days > 0:
        day += timedelta(days=1)
        if day.weekday() < 5:
            days -= 1
    return day


class CheckoutSettings(models.Model):
    """Shop-wide checkout settings the owner changes in the admin (one row)."""

    free_shipping_over = models.DecimalField(
        "free shipping from", max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Orders of at least this much (after discounts) ship free by the cheapest service.  "
        "Empty: no free shipping.",
    )
    ship_within_days = models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Working days after payment within which orders ship.  Customers are told this; the law "
        "(the FTC Mail Order Rule) holds you to it.",
    )
    vacation_mode = models.BooleanField(
        default=False, help_text="You are away: customers see a notice, and orders ship from the date below"
    )
    vacation_message = models.CharField(
        max_length=300, blank=True,
        help_text='Shown at the top of every shop page, e.g. "We are away until June 12; orders ship from then."',
    )
    vacation_ships_from = models.DateField(
        null=True, blank=True, help_text="The first day you can ship again"
    )
    vacation_pause_orders = models.BooleanField(
        "stop taking orders", default=False,
        help_text="While on vacation, close the checkout instead of taking orders that ship later",
    )

    class Meta:
        verbose_name = verbose_name_plural = "checkout settings"

    def __str__(self):
        return "Checkout settings"

    @classmethod
    def current(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def clean(self):
        if self.vacation_mode and not (self.vacation_message or self.vacation_ships_from):
            raise ValidationError("Give customers a message or the date you ship again.")

    def on_vacation(self, day=None):
        day = day or timezone.localdate()
        if not self.vacation_mode:
            return False
        return self.vacation_ships_from is None or self.vacation_ships_from > day

    def taking_orders(self):
        return not (self.on_vacation() and self.vacation_pause_orders)

    def ship_by(self, day=None):
        """The date an order paid on day (default today) is promised to
        ship by: after the vacation, plus the working days."""
        day = day or timezone.localdate()
        if self.on_vacation(day) and self.vacation_ships_from:
            day = self.vacation_ships_from - timedelta(days=1)
        return add_business_days(day, self.ship_within_days)


class AddressFields(models.Model):
    """A US shipping address (48 contiguous states and DC)."""

    ship_name = models.CharField("name", max_length=100, blank=True)
    ship_street1 = models.CharField("street address", max_length=100, blank=True)
    ship_street2 = models.CharField("apartment, suite etc.", max_length=100, blank=True)
    ship_city = models.CharField("city", max_length=60, blank=True)
    ship_state = models.CharField("state", max_length=2, choices=SHIPPING_STATES, blank=True)
    ship_zip = models.CharField(
        "ZIP code", max_length=10, blank=True, validators=[RegexValidator(r"^\d{5}(-\d{4})?$", "A 5-digit ZIP code")]
    )
    ship_phone = models.CharField("phone", max_length=30, blank=True)

    ADDRESS_FIELDS = ["name", "street1", "street2", "city", "state", "zip", "phone"]

    class Meta:
        abstract = True

    @property
    def address(self):
        from .shipping import Address

        return Address(**{name: getattr(self, f"ship_{name}") for name in self.ADDRESS_FIELDS})

    def set_address(self, address):
        for name in self.ADDRESS_FIELDS:
            setattr(self, f"ship_{name}", getattr(address, name))

    @property
    def has_address(self):
        return bool(self.ship_street1 and self.ship_zip)

    def address_lines(self):
        lines = [self.ship_name, self.ship_street1, self.ship_street2,
                 f"{self.ship_city}, {self.ship_state} {self.ship_zip}"]
        return [line for line in lines if line]


class Customer(AddressFields):
    """A customer who signed in with a link sent to their email: no
    password to keep or leak.  Signing in shows every order placed with
    that email, including those placed as a guest."""

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    last_sign_in_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def orders(self):
        return Order.objects.filter(models.Q(customer=self) | models.Q(email__iexact=self.email)).exclude(
            status=Order.Status.PENDING)


class DiscountCode(models.Model):
    """A public code anyone may use: prices stay the same for everyone,
    never set per person (see docs/checkout.md, "Prices")."""

    class Kind(models.TextChoices):
        PERCENT = "percent", "Percent off the items"
        AMOUNT = "amount", "Dollars off the items"
        FREE_SHIPPING = "free_shipping", "Free shipping (cheapest service)"

    code = models.CharField(
        max_length=30, unique=True,
        validators=[RegexValidator(r"^[A-Z0-9-]+$", "Capital letters, digits and dashes")],
        help_text="What customers type, e.g. SPRING10 (capital letters, digits, dashes)",
    )
    description = models.CharField(max_length=200, blank=True, help_text="For you: what it is for")
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.PERCENT)
    value = models.DecimalField(
        max_digits=8, decimal_places=2, default=ZERO, validators=[MinValueValidator(0)],
        help_text="Percent (10 for 10%) or dollars; not used for free shipping",
    )
    min_subtotal = models.DecimalField(
        "minimum order", max_digits=8, decimal_places=2, default=ZERO, validators=[MinValueValidator(0)],
        help_text="Items must come to at least this much",
    )
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True, help_text="Last day it works")
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Paid orders it can be used on in all")
    once_per_customer = models.BooleanField(default=False, help_text="Once per email address")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code

    def clean(self):
        self.code = (self.code or "").strip().upper()
        if self.kind == self.Kind.PERCENT and not (0 < self.value <= 100):
            raise ValidationError({"value": "A percentage from 1 to 100."})
        if self.kind == self.Kind.AMOUNT and self.value <= 0:
            raise ValidationError({"value": "How many dollars off."})
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValidationError({"ends_on": "The end date is before the start date."})

    def uses(self):
        return self.orders.filter(status__in=Order.PAID_STATUSES).count()

    def problem(self, subtotal, email="", day=None):
        """None if the code can be used on items worth subtotal, else why not
        (for the customer)."""
        day = day or timezone.localdate()
        if not self.is_active or (self.starts_on and day < self.starts_on) or (self.ends_on and day > self.ends_on):
            return f"The code {self.code} is not valid now."
        if self.max_uses is not None and self.uses() >= self.max_uses:
            return f"The code {self.code} has been used up."
        if subtotal < self.min_subtotal:
            return f"The code {self.code} needs an order of at least ${self.min_subtotal:,.2f}."
        if email and self.once_per_customer and self.orders.filter(
                status__in=Order.PAID_STATUSES, email__iexact=email).exists():
            return f"The code {self.code} can be used once per customer, and you have used it."
        return None

    def amount_off(self, subtotal):
        if self.kind == self.Kind.PERCENT:
            return min(subtotal, (subtotal * self.value / 100).quantize(CENT))
        if self.kind == self.Kind.AMOUNT:
            return min(subtotal, self.value)
        return ZERO


class Cart(models.Model):
    """A visitor's cart, found through their session (or account)."""

    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="carts")
    discount = models.ForeignKey(DiscountCode, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.pk}"

    def item_count(self):
        return sum(line.quantity for line in self.lines.all())


class CartLine(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="lines")
    size_option = models.ForeignKey(SizeOption, on_delete=models.CASCADE, related_name="+")
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["pk"]
        constraints = [models.UniqueConstraint(fields=["cart", "size_option"], name="checkout_cart_size_once")]

    def __str__(self):
        return f"{self.quantity} × {self.size_option}"


class Order(AddressFields):
    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for payment"
        PAID = "paid", "Paid, to pack"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"

    PAID_STATUSES = (Status.PAID, Status.SHIPPED)

    number = models.CharField(max_length=20, unique=True, editable=False)
    token = models.CharField(max_length=40, unique=True, default=new_token, editable=False,
                             help_text="The secret in the customer's order-status link")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    email = models.EmailField()
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    subscription = models.ForeignKey("Subscription", null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="orders", help_text="A subscription delivery")
    cart_id = models.IntegerField(null=True, blank=True, editable=False)
    address_verified = models.BooleanField(default=False, help_text="The address checker confirmed it")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO, help_text="Items before discount")
    discount = models.ForeignKey(DiscountCode, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    discount_code = models.CharField(max_length=30, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    shipping_service = models.CharField(max_length=60, blank=True)
    shipping_rate_id = models.CharField(max_length=80, blank=True, help_text="The rate quoted (for the label)")
    shipping_shipment_id = models.CharField(max_length=80, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO,
                                        help_text="What the postage costs the shop")
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO,
                                          help_text="What the customer paid for shipping")
    tax_rate = models.DecimalField(max_digits=7, decimal_places=5, default=Decimal("0"))
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO,
                                         help_text="Taxable items after discount, plus their share of shipping")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    tax_jurisdiction = models.CharField(max_length=100, blank=True)
    tax_fallback = models.BooleanField(default=False, help_text="No rate was entered for this ZIP code; the "
                                       "state's fallback rate was charged")
    tax_calculation_id = models.CharField(max_length=80, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)

    payment_provider = models.CharField(max_length=20, blank=True)
    payment_id = models.CharField(max_length=80, blank=True, db_index=True)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True, db_index=True)
    ship_by = models.DateField(null=True, blank=True, help_text="Promised to ship by (FTC Mail Order Rule)")
    shipped_at = models.DateTimeField(null=True, blank=True)
    carrier = models.CharField(max_length=30, blank=True, default="USPS")
    tracking_number = models.CharField(max_length=60, blank=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    shipped_email_sent_at = models.DateTimeField(null=True, blank=True)
    owner_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"Order {self.number}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.make_number()
        super().save(*args, **kwargs)

    @staticmethod
    def make_number():
        prefix = timezone.localdate().strftime("%y%m%d")
        while True:
            number = f"{prefix}-{''.join(secrets.choice(_NUMBER_ALPHABET) for _ in range(4))}"
            if not Order.objects.filter(number=number).exists():
                return number

    def get_absolute_url(self):
        return reverse("checkout:order_status", args=[self.token])

    @property
    def is_paid(self):
        return self.status in self.PAID_STATUSES

    @property
    def total_cents(self):
        return int((self.total * 100).to_integral_value())

    @property
    def state_name(self):
        return STATE_NAMES.get(self.ship_state, self.ship_state)

    def tracking_url(self):
        if not self.tracking_number:
            return ""
        if self.carrier.upper() == "USPS":
            return f"https://tools.usps.com/go/TrackConfirmAction?tLabels={self.tracking_number}"
        return ""


class OrderLine(models.Model):
    class Kind(models.TextChoices):
        TEA = "tea", "Tea (no sales tax in NY)"
        GOODS = "goods", "Merchandise (taxable)"
        SUBSCRIPTION = "subscription", "Subscription delivery"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    size_option = models.ForeignKey(SizeOption, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    product_name = models.CharField(max_length=150)
    size_name = models.CharField(max_length=60, blank=True)
    sku = models.CharField(max_length=40, blank=True)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    discount_share = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    taxable = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return f"{self.quantity} × {self.product_name} {self.size_name}".strip()

    @property
    def net_amount(self):
        return self.line_total - self.discount_share


class TaxRate(models.Model):
    """The combined state and local sales tax rate for deliveries to a
    ZIP code (5 digits), a ZIP area (its first 3 digits), or a whole state
    (blank).  The longest match wins.  For New York, see Publication 718
    and the Department of Taxation's address lookup."""

    state = models.CharField(max_length=2, choices=SHIPPING_STATES, default="NY")
    zip_prefix = models.CharField(
        "ZIP code or start", max_length=5, blank=True,
        validators=[RegexValidator(r"^(\d{3}|\d{5})?$", "3 or 5 digits, or empty for the whole state")],
        help_text="5 digits for one ZIP code, 3 for every ZIP code starting so, empty for the whole state",
    )
    rate = models.DecimalField(
        max_digits=6, decimal_places=5, validators=[MinValueValidator(0), MaxValueValidator(Decimal("0.2"))],
        help_text="As a fraction: 0.08 for 8%, 0.08875 for 8.875%",
    )
    jurisdiction = models.CharField(max_length=100, help_text='e.g. "Albany County" or "City of Oneida"')
    notes = models.CharField(max_length=200, blank=True)
    checked_on = models.DateField(default=timezone.localdate, help_text="When you last checked the rate")

    class Meta:
        ordering = ["state", "zip_prefix"]
        constraints = [models.UniqueConstraint(fields=["state", "zip_prefix"], name="checkout_tax_rate_once")]

    def __str__(self):
        return f"{self.state} {self.zip_prefix or '(all)'}: {self.rate * 100:.3f}% {self.jurisdiction}"

    @classmethod
    def lookup(cls, state, zip_code):
        zip5 = (zip_code or "")[:5]
        candidates = [zip5, zip5[:3], ""]
        rates = {rate.zip_prefix: rate for rate in cls.objects.filter(state=state, zip_prefix__in=candidates)}
        for prefix in candidates:
            if prefix in rates:
                return rates[prefix]
        return None


class NexusThreshold(models.Model):
    """A state's economic-nexus threshold for remote sellers: once sales
    into it pass this in the current or previous calendar year, the shop
    must register and collect that state's sales tax.  The starting
    figures are a summary; check each state's own guidance before relying
    on them."""

    state = models.CharField(max_length=2, choices=SHIPPING_STATES, unique=True)
    has_sales_tax = models.BooleanField(default=True)
    sales = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                help_text="Gross sales into the state in a year")
    transactions = models.PositiveIntegerField(null=True, blank=True, help_text="Orders into the state in a year")
    needs_both = models.BooleanField(default=False, help_text="Both must be passed (New York); else either")
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["state"]

    def __str__(self):
        return f"{self.get_state_display()} nexus threshold"


class WebhookEvent(models.Model):
    """Stripe events already handled, so a resent event is not handled twice."""

    event_id = models.CharField(max_length=80, unique=True)
    type = models.CharField(max_length=80)
    received_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.type} {self.event_id}"


class SubscriptionPlan(models.Model):
    """A tea subscription customers can sign up for.  Each delivery is
    tea only (no sales tax in New York), shipping included in the price."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(help_text="What each delivery holds, e.g. two 50 g pouches of the month's teas")
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("1.00"))],
                                help_text="Per renewal, shipping included.  A change applies to new subscribers; "
                                "tell existing ones before charging them more.")
    interval_months = models.PositiveSmallIntegerField(
        "renews every (months)", default=1, validators=[MinValueValidator(1), MaxValueValidator(12)])
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    stripe_product_id = models.CharField(max_length=80, blank=True, editable=False)

    class Meta:
        ordering = ["sort_order", "price"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("checkout:subscribe", args=[self.slug])

    def clean(self):
        from apps.catalog import copy_rules

        errors = {}
        for name in ("name", "description"):
            problems = copy_rules.health_claim_problems(getattr(self, name), name.capitalize())
            if problems:
                errors[name] = problems
        if errors:
            raise ValidationError(errors)

    @property
    def interval_text(self):
        if self.interval_months == 1:
            return "every month"
        if self.interval_months == 12:
            return "every year"
        return f"every {self.interval_months} months"

    def renewal_terms(self):
        """The automatic renewal terms, shown next to the sign-up button and
        repeated in the acknowledgment email (NY GBL 527-a, Cal. Bus. &
        Prof. Code 17602)."""
        return (
            f"Your subscription renews automatically {self.interval_text} until you cancel.  "
            f"We charge ${self.price:,.2f} (shipping included; tea has no sales tax) to your payment method today "
            f"and again at each renewal.  Cancel any time online, in one step, from your account or the link in "
            f"every subscription email; cancelling stops all future charges, and the delivery you have paid for "
            f"still ships."
        )


class Subscription(AddressFields):
    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for the first payment"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Renewal payment failed"
        CANCELLED = "cancelled", "Cancelled; no more renewals"
        ENDED = "ended", "Ended"

    LIVE_STATUSES = (Status.ACTIVE, Status.PAST_DUE)

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="subscriptions")
    email = models.EmailField()
    token = models.CharField(max_length=40, unique=True, default=new_token, editable=False,
                             help_text="The secret in the customer's cancel link")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    interval_months = models.PositiveSmallIntegerField()
    terms_text = models.TextField(help_text="The renewal terms the customer agreed to")
    consented_at = models.DateTimeField(help_text="When the customer ticked the consent box")
    payment_provider = models.CharField(max_length=20, blank=True)
    stripe_customer_id = models.CharField(max_length=80, blank=True)
    stripe_subscription_id = models.CharField(max_length=80, blank=True, db_index=True)
    current_period_end = models.DateTimeField(null=True, blank=True, help_text="The next renewal")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    acknowledgment_sent_at = models.DateTimeField(null=True, blank=True)
    reminded_for = models.DateTimeField(null=True, blank=True, editable=False,
                                        help_text="The renewal the last reminder was about")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.plan} for {self.email}"

    @property
    def is_live(self):
        return self.status in self.LIVE_STATUSES

    def cancel_url(self):
        return reverse("checkout:subscription_cancel", args=[self.token])

    def card_url(self):
        """The page for paying with a different card (no sign-in, like the
        cancel link)."""
        return reverse("checkout:subscription_card", args=[self.token])
