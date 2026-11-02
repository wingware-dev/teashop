"""Packing and shipping orders.

An order is shipped in one or more parcels.  Each Parcel lists the order
lines (and quantities) it carries: the first parcel holds the whole order;
shipping only part of it moves the rest to a back-ordered parcel; a reship
of a lost or damaged parcel is a new parcel of the same order.

Packing a package (services.pack_package) weighs the tea on a legal-for-
trade Scale, takes it and the packaging from stock (catalog.services.pack)
and records a PackedPackage: the measured net weight and the scale used,
with its seal date, as the weights and measures rules want kept.

A PostageLabel is the postage bought for a parcel, with the box used; a
Pickup is a free USPS carrier pickup.  Refunds and Mail Order Rule delay
notices belong to the order.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.catalog.models import SizeOption, SoldPackage
from apps.checkout.models import Order, OrderLine
from apps.inventory.models import Item
from apps.inventory.storage import private_storage

ZERO = Decimal("0.00")


class Scale(models.Model):
    """The scale tea is weighed on for sale.  It must be NTEP-approved
    (legal for trade), registered with the county weights and measures
    office, and inspected and sealed by them; again after any repair or
    recalibration."""

    name = models.CharField(max_length=80, help_text='What you call it, e.g. "Bench scale"')
    make_model = models.CharField("make and model", max_length=120, blank=True)
    serial_number = models.CharField(max_length=60, help_text="The scale's serial number (its ID on the records)")
    ntep_certificate = models.CharField("NTEP certificate", max_length=40, blank=True,
                                        help_text="The Certificate of Conformance number on the scale's plate")
    registration = models.CharField(max_length=60, blank=True,
                                    help_text="The county weights and measures registration or permit number")
    sealed_on = models.DateField("sealed or calibrated on",
                                 help_text="When weights and measures last inspected and sealed it")
    inspection_due = models.DateField(null=True, blank=True, help_text="When the next inspection is due, if known")
    seal_intact = models.BooleanField(default=True, help_text="Untick if the seal is broken (after a repair, say); "
                                      "then it can't be used for packing until it is sealed again")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "name"]

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

    @property
    def usable(self):
        return self.is_active and self.seal_intact

    def inspection_overdue(self, day=None):
        day = day or timezone.localdate()
        return bool(self.inspection_due and self.inspection_due < day)


class BoxSize(models.Model):
    """A shipping box or mailer you keep, with its inside size: the box
    suggestion picks the smallest that holds an order."""

    item = models.OneToOneField(Item, on_delete=models.PROTECT, related_name="box_size",
                                limit_choices_to={"kind": Item.Kind.SHIPPING_BOX},
                                help_text="The stock item (kind: shipping box) that goes down when one is used")
    length_in = models.DecimalField("inside length (in)", max_digits=5, decimal_places=2,
                                    validators=[MinValueValidator(Decimal("0.1"))])
    width_in = models.DecimalField("inside width (in)", max_digits=5, decimal_places=2,
                                   validators=[MinValueValidator(Decimal("0.1"))])
    height_in = models.DecimalField("inside height (in)", max_digits=5, decimal_places=2,
                                    validators=[MinValueValidator(Decimal("0.1"))],
                                    help_text="For a padded mailer, how thick it can be when full")
    empty_grams = models.PositiveIntegerField("weight empty (g)", default=0)
    max_grams = models.PositiveIntegerField("most it holds (g)", null=True, blank=True,
                                            help_text="Empty: no limit but the postage service's")
    filler = models.ForeignKey(Item, null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"kind": Item.Kind.PACKAGING},
                               help_text="Filler or padding used with this box (stock goes down too)")
    filler_quantity = models.PositiveSmallIntegerField(default=0, help_text="Pieces of filler per box")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["length_in", "width_in", "height_in"]
        verbose_name = "box size"

    def __str__(self):
        return f"{self.item.name} ({self.dimensions_text})"

    def clean(self):
        if self.filler_quantity and not self.filler_id:
            raise ValidationError({"filler": "Choose the filler, or set the quantity to 0."})

    @property
    def dimensions(self):
        return sorted([self.length_in, self.width_in, self.height_in], reverse=True)

    @property
    def dimensions_text(self):
        return " × ".join(f"{d.normalize():f}" for d in (self.length_in, self.width_in, self.height_in)) + " in"

    @property
    def volume(self):
        return self.length_in * self.width_in * self.height_in

    def in_stock(self):
        return self.item.on_hand() >= 1


class PackageDimensions(models.Model):
    """Outside size of one packed package of a size option, for the box
    suggestion.  Sizes without one use a usual size for their package
    (settings.PACKAGE_DIMENSIONS_IN)."""

    size_option = models.OneToOneField(SizeOption, on_delete=models.CASCADE, related_name="dimensions")
    length_in = models.DecimalField("length (in)", max_digits=5, decimal_places=2,
                                    validators=[MinValueValidator(Decimal("0.1"))])
    width_in = models.DecimalField("width (in)", max_digits=5, decimal_places=2,
                                   validators=[MinValueValidator(Decimal("0.1"))])
    height_in = models.DecimalField("height (in)", max_digits=5, decimal_places=2,
                                    validators=[MinValueValidator(Decimal("0.1"))])

    class Meta:
        verbose_name = verbose_name_plural = "package dimensions"

    def __str__(self):
        return f"{self.size_option}: {self.length_in} × {self.width_in} × {self.height_in} in"


class Pickup(models.Model):
    """A free USPS carrier pickup of the day's parcels."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CANCELLED = "cancelled", "Cancelled"

    pickup_date = models.DateField()
    location = models.CharField(max_length=60, default="Front door",
                                help_text='Where the carrier finds the parcels, e.g. "Front door", "Side door"')
    instructions = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED)
    provider = models.CharField(max_length=20, blank=True)
    provider_id = models.CharField(max_length=80, blank=True)
    confirmation = models.CharField(max_length=80, blank=True, help_text="USPS confirmation number")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-pickup_date", "-pk"]

    def __str__(self):
        return f"USPS pickup {self.pickup_date:%Y-%m-%d}" + (f" ({self.confirmation})" if self.confirmation else "")


class Parcel(models.Model):
    """One box shipped (or to be shipped) for an order."""

    class Kind(models.TextChoices):
        ORDER = "order", "Order"
        BACKORDER = "backorder", "Back-ordered rest"
        RESHIP = "reship", "Reship (lost or damaged)"

    class Status(models.TextChoices):
        OPEN = "open", "To pack"
        BACKORDERED = "backordered", "Back-ordered"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"

    ACTIVE_STATUSES = (Status.OPEN, Status.BACKORDERED)

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="parcels")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.ORDER)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN, db_index=True)
    reason = models.CharField(max_length=300, blank=True, help_text="Why it was reshipped or back-ordered")
    expected_on = models.DateField(null=True, blank=True, help_text="Back-ordered: when the stock is expected")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    shipped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return f"{self.get_kind_display()} parcel for order {self.order.number}"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    def live_packages(self):
        return self.packages.filter(sold_package__reversed_at=None).select_related(
            "sold_package__size_option__product", "sold_package__tea_lot", "scale", "order_line")

    def current_label(self):
        return self.labels.filter(voided_at=None).order_by("-pk").first()


class ParcelLine(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name="lines")
    order_line = models.ForeignKey(OrderLine, on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["parcel", "order_line"]
        constraints = [models.UniqueConstraint(fields=["parcel", "order_line"], name="fulfillment_parcel_line_once")]

    def __str__(self):
        return f"{self.quantity} × {self.order_line.product_name} {self.order_line.size_name}".strip()


class PackedPackage(models.Model):
    """The packing record of one package: what the scale showed and which
    scale it was, kept for weights and measures (the label promises at
    least the net weight)."""

    parcel = models.ForeignKey(Parcel, on_delete=models.PROTECT, related_name="packages")
    order_line = models.ForeignKey(OrderLine, on_delete=models.PROTECT, related_name="+")
    sold_package = models.OneToOneField(SoldPackage, on_delete=models.PROTECT, related_name="packing")
    measured_grams = models.DecimalField("measured net weight (g)", max_digits=8, decimal_places=1, null=True,
                                         blank=True, help_text="Tea only: what the scale showed, less the tare")
    scale = models.ForeignKey(Scale, null=True, blank=True, on_delete=models.PROTECT, related_name="packages")
    # The scale's ID and seal date as they were when it was used, so the
    # record stands even if the scale's details change later.
    scale_serial = models.CharField(max_length=60, blank=True)
    scale_sealed_on = models.DateField(null=True, blank=True)
    allergens_confirmed = models.BooleanField(default=False,
                                              help_text="The packer confirmed allergen handling (separate scoop, "
                                              "clean afterwards)")
    packed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+")
    packed_at = models.DateTimeField(default=timezone.now)
    label_printed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["parcel", "pk"]

    def __str__(self):
        return f"{self.sold_package}"

    @property
    def reversed(self):
        return self.sold_package.reversed_at is not None


def label_path(label, filename):
    return f"shipping-labels/{timezone.now():%Y/%m}/{filename}"


class PostageLabel(models.Model):
    """Postage bought for a parcel, and the box it went in."""

    parcel = models.ForeignKey(Parcel, on_delete=models.PROTECT, related_name="labels")
    provider = models.CharField(max_length=20)
    test_mode = models.BooleanField(default=True, help_text="A test label: no postage paid, not for mailing")
    shipment_id = models.CharField(max_length=80, blank=True)
    carrier = models.CharField(max_length=30, default="USPS")
    service = models.CharField(max_length=60)
    tracking_number = models.CharField(max_length=60)
    postage = models.DecimalField(max_digits=8, decimal_places=2, default=ZERO, help_text="What the postage cost")
    weight_grams = models.PositiveIntegerField()
    box = models.ForeignKey(BoxSize, null=True, blank=True, on_delete=models.PROTECT, related_name="labels")
    box_suggested = models.ForeignKey(BoxSize, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    box_description = models.CharField(max_length=120, blank=True, help_text="A box not in the list")
    length_in = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    width_in = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_in = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    label_file = models.FileField(upload_to=label_path, storage=private_storage, blank=True)
    label_format = models.CharField(max_length=4, default="PDF")
    pickup = models.ForeignKey(Pickup, null=True, blank=True, on_delete=models.SET_NULL, related_name="labels")
    bought_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+")
    bought_at = models.DateTimeField(default=timezone.now)
    printed_at = models.DateTimeField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True, help_text="Refund of the postage asked for")
    void_status = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["-bought_at", "-pk"]

    def __str__(self):
        return f"{self.carrier} {self.tracking_number}"

    @property
    def box_text(self):
        if self.box_id:
            return self.box.item.name
        return self.box_description or "Other box"


class Refund(models.Model):
    class Kind(models.TextChoices):
        FULL = "full", "Full refund"
        PARTIAL = "partial", "Partial refund"
        CANCELLATION = "cancellation", "Order cancelled"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="refunds")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    taxable_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="The part of the order's taxable amount refunded (taxable items and their share of shipping)")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"),
                                     help_text="The sales tax given back, included in the amount")
    reason = models.CharField(max_length=300)
    provider = models.CharField(max_length=20, blank=True)
    provider_id = models.CharField(max_length=80, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="+")
    created_at = models.DateTimeField(default=timezone.now)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"${self.amount:,.2f} refund for order {self.order.number}"


class DelayNotice(models.Model):
    """A Mail Order Rule delay notice: the order can't ship by the date
    promised, so the customer is told the new date and offered to cancel
    for a full refund.  For a delay of up to 30 days (the first notice
    only), saying nothing is consent; otherwise the customer must agree, or
    the order is cancelled and refunded."""

    class Response(models.TextChoices):
        WAITING = "waiting", "No answer yet"
        CONSENTED = "consented", "Agreed to wait"
        CANCELLED = "cancelled", "Cancelled the order"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="delay_notices")
    old_ship_by = models.DateField()
    new_ship_by = models.DateField()
    reason = models.CharField(max_length=300, help_text="Shown to the customer, e.g. \"Our Assam is on its way from "
                              "the importer\"")
    needs_consent = models.BooleanField(default=False,
                                        help_text="The order is cancelled unless the customer agrees to wait")
    answer_by = models.DateField(null=True, blank=True,
                                 help_text="Needing consent: cancel and refund if no answer by this day")
    response = models.CharField(max_length=10, choices=Response.choices, default=Response.WAITING)
    responded_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"Delay notice for order {self.order.number}: ship by {self.new_ship_by:%Y-%m-%d}"

    @property
    def awaiting_consent(self):
        return self.needs_consent and self.response == self.Response.WAITING
