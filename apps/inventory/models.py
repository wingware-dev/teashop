"""Stock: items, suppliers, lots, stock movements, purchase orders,
receiving, and recipes for blends.

Quantities are whole numbers in the item's unit: grams for bulk items
(tea, herbal ingredients, flavourings), pieces for everything else.

Every gram or piece in stock belongs to a lot, and every change to a lot's
quantity is a StockMovement, so the history of a lot can always be read
back: where it came from, which blends used it, and which customer orders
received it (see tracing.py).
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone

from .storage import document_path, private_storage, validate_document_extension


class AppendOnlyError(Exception):
    """Raised on an attempt to change or delete a recorded stock movement."""


def format_quantity(quantity, by_weight):
    if quantity is None:
        return ""
    return f"{quantity:,} g" if by_weight else f"{quantity:,}"


class Allergen(models.Model):
    """One of the major food allergens US labels must declare."""

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=150, unique=True)
    contact_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    lead_time_days = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Usual days from ordering to delivery"
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Item(models.Model):
    """Something kept in stock: a bulk tea, a tin, a label, a mug."""

    class Kind(models.TextChoices):
        TEA = "tea", "Tea (bulk, by weight)"
        HERBAL = "herbal", "Herbal ingredient (bulk, by weight)"
        INGREDIENT = "ingredient", "Flavouring or other blend ingredient (by weight)"
        PACKAGING = "packaging", "Packaging: pouches, tins, labels, filler (by unit)"
        SHIPPING_BOX = "shipping_box", "Shipping box or mailer (by unit)"
        MERCH = "merch", "Merchandise (by unit)"
        ACCESSORY = "accessory", "Accessory (by unit)"

    BY_WEIGHT = (Kind.TEA, Kind.HERBAL, Kind.INGREDIENT)
    # Kinds that name a country on the label ("Grown in ...").
    GROWN = (Kind.TEA, Kind.HERBAL)

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r"^[A-Z0-9]+(-[A-Z0-9]+)*$", "Capital letters, digits and dashes, e.g. ASSAM-TGFOP")],
        help_text="Short code, the start of every lot code (ASSAM becomes lot ASSAM-261101)",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    ingredient_name = models.CharField(
        max_length=150,
        blank=True,
        help_text='How this reads in an ingredient list, e.g. "black tea" or "natural vanilla flavour"',
    )
    reorder_level = models.PositiveIntegerField(
        default=0,
        help_text="Alert when usable stock falls to this or below (grams for bulk items, pieces otherwise); 0 for no alert",
    )
    default_supplier = models.ForeignKey(
        Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def by_weight(self):
        return self.kind in self.BY_WEIGHT

    @property
    def unit(self):
        return "g" if self.by_weight else "pieces"

    def format_quantity(self, quantity):
        return format_quantity(quantity, self.by_weight)

    def usable_lots(self):
        """Lots that can be drawn from, oldest best-by first (FEFO)."""
        return self.lots.usable().order_by(models.F("best_by").asc(nulls_last=True), "received_on", "pk")

    def on_hand(self):
        """Usable stock: lots on hold or recalled don't count."""
        return self.lots.usable().aggregate(total=Sum("quantity_on_hand"))["total"] or 0

    def is_low(self):
        return self.reorder_level > 0 and self.on_hand() <= self.reorder_level


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ORDERED = "ordered", "Ordered"
        PARTIAL = "partial", "Partly received"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    reference = models.CharField(max_length=60, blank=True, help_text="Your PO number or the supplier's order number")
    ordered_on = models.DateField(null=True, blank=True)
    expected_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        label = self.reference or f"PO {self.pk}"
        return f"{label} ({self.supplier})"

    def refresh_status(self):
        """Partly received or received, from the lots received against it."""
        if self.status == self.Status.CANCELLED:
            return
        lines = list(self.lines.all())
        received = [line.quantity_received() for line in lines]
        if lines and all(got >= line.quantity for got, line in zip(received, lines)):
            status = self.Status.RECEIVED
        elif any(received):
            status = self.Status.PARTIAL
        else:
            return
        if status != self.status:
            self.status = status
            self.save(update_fields=["status"])


class PurchaseOrderLine(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="purchase_order_lines")
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], help_text="Grams for bulk items, pieces otherwise"
    )
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price per kg for bulk items, per piece otherwise"
    )

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return f"{self.item}: {self.item.format_quantity(self.quantity)} on {self.order}"

    def quantity_received(self):
        return self.lots.aggregate(total=Sum("quantity_received"))["total"] or 0

    def quantity_outstanding(self):
        return max(self.quantity - self.quantity_received(), 0)


class Receipt(models.Model):
    """One delivery.  It may fill a purchase order only partly; the rest
    comes in a later receipt against the same order."""

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="receipts")
    purchase_order = models.ForeignKey(
        PurchaseOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="receipts"
    )
    received_on = models.DateField(default=timezone.localdate)
    packing_slip = models.FileField(
        upload_to=document_path,
        storage=private_storage,
        blank=True,
        validators=[validate_document_extension],
        help_text="Packing slip or invoice (kept private)",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_on", "-pk"]

    def __str__(self):
        return f"Delivery from {self.supplier} on {self.received_on:%Y-%m-%d}"

    def clean(self):
        if self.purchase_order_id and self.supplier_id and self.purchase_order.supplier_id != self.supplier_id:
            raise ValidationError({"purchase_order": "This purchase order is with another supplier."})


class LotQuerySet(models.QuerySet):
    def usable(self):
        return self.filter(status=Lot.Status.ACTIVE, quantity_on_hand__gt=0)


class Lot(models.Model):
    """A quantity of one item with one origin: a supplier delivery, or a
    blend batch made here."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_HOLD = "on_hold", "On hold"
        RECALLED = "recalled", "Recalled"

    class Source(models.TextChoices):
        RECEIVED = "received", "Received from supplier"
        BLENDED = "blended", "Blended here"

    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="lots")
    code = models.CharField(
        max_length=40, unique=True, blank=True, help_text="Printed on labels; made from the item code and date if left blank"
    )
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.RECEIVED, editable=False)
    receipt = models.ForeignKey(Receipt, null=True, blank=True, on_delete=models.PROTECT, related_name="lots")
    purchase_order_line = models.ForeignKey(
        PurchaseOrderLine, null=True, blank=True, on_delete=models.PROTECT, related_name="lots"
    )
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.PROTECT, related_name="lots")
    supplier_lot_code = models.CharField(max_length=60, blank=True, help_text="The supplier's own lot or batch number")
    quantity_received = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Grams for bulk items, pieces otherwise.  Fixed once saved: correct mistakes with a stock adjustment.",
    )
    quantity_on_hand = models.IntegerField(default=0, editable=False)
    received_on = models.DateField(default=timezone.localdate)
    harvest_year = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1950), MaxValueValidator(2100)]
    )
    best_by = models.DateField(null=True, blank=True)
    country_of_origin = models.CharField(
        max_length=150,
        blank=True,
        help_text='Where it was grown, as printed after "Grown in" (e.g. "Sri Lanka"); blends list each country',
    )
    organic = models.BooleanField(default=False, help_text="Certified organic by the supplier (keep the certificate as a document)")
    ingredients = models.CharField(
        max_length=500, blank=True, help_text="Ingredient wording for the label; the item's ingredient name if left blank"
    )
    allergens = models.ManyToManyField(Allergen, blank=True, related_name="lots")
    allergen_statement = models.TextField(blank=True, help_text="The supplier's allergen statement, word for word")
    landed_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost per kg for bulk items, per piece otherwise, including shipping, tariffs and duties",
    )
    tariff_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="The part of the landed cost that is tariffs and duties"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    status_note = models.CharField(max_length=300, blank=True, help_text="Why the lot is on hold or recalled")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LotQuerySet.as_manager()

    class Meta:
        ordering = ["item__name", models.F("best_by").asc(nulls_last=True), "received_on", "pk"]

    def __str__(self):
        return f"{self.code} ({self.item})"

    def get_absolute_url(self):
        return reverse("admin:inventory_lot_change", args=[self.pk])

    def format_quantity(self, quantity):
        return self.item.format_quantity(quantity)

    def clean(self):
        errors = {}
        item = self.item if self.item_id else None
        if self.landed_cost is not None and self.tariff_cost is not None and self.tariff_cost > self.landed_cost:
            errors["tariff_cost"] = "Tariffs are part of the landed cost, so cannot be more than it."
        if self.purchase_order_line_id:
            line = self.purchase_order_line
            # The receipt may be unsaved, when the lot is a line of a new delivery.
            receipt = self.receipt
            if item and line.item_id != item.pk:
                errors["purchase_order_line"] = f"That order line is for {line.item}, not {item}."
            elif receipt is not None and receipt.purchase_order_id not in (None, line.order_id):
                errors["purchase_order_line"] = "That line is on a different purchase order from this delivery."
        if item and item.by_weight and self.source == self.Source.RECEIVED:
            if not self.best_by:
                errors["best_by"] = "Bulk items need a best-by date for the label."
            if item.kind in Item.GROWN and not self.country_of_origin.strip():
                errors["country_of_origin"] = 'Teas and herbs need a country of origin for the "Grown in" line.'
        if self.pk and self.quantity_received != self._stored_quantity_received():
            errors["quantity_received"] = "The received quantity is fixed; record a stock adjustment instead."
        if errors:
            raise ValidationError(errors)

    def _stored_quantity_received(self):
        return Lot.objects.filter(pk=self.pk).values_list("quantity_received", flat=True).first()

    def make_code(self):
        day = self.received_on or timezone.localdate()
        base = f"{self.item.code}-{day:%y%m%d}"
        code, n = base, 1
        while Lot.objects.filter(code=code).exclude(pk=self.pk).exists():
            n += 1
            code = f"{base}-{n}"
        return code

    def save(self, *args, **kwargs):
        adding = self._state.adding
        if not adding and self.quantity_received != self._stored_quantity_received():
            raise ValidationError("A lot's received quantity cannot change; record a stock adjustment instead.")
        if self.receipt_id:
            self.supplier_id = self.supplier_id or self.receipt.supplier_id
            if adding:
                self.received_on = self.receipt.received_on
        if not self.code:
            self.code = self.make_code()
        if not self.ingredients and self.item_id:
            self.ingredients = self.item.ingredient_name
        with transaction.atomic():
            super().save(*args, **kwargs)
            if adding:
                kind = (
                    StockMovement.Kind.BLEND_OUTPUT if self.source == self.Source.BLENDED else StockMovement.Kind.RECEIPT
                )
                StockMovement.objects.create(lot=self, quantity=self.quantity_received, kind=kind)
                Lot.objects.filter(pk=self.pk).update(quantity_on_hand=self.quantity_received)
                self.quantity_on_hand = self.quantity_received
                if self.purchase_order_line_id:
                    self.purchase_order_line.order.refresh_status()

    @property
    def usable(self):
        return self.status == self.Status.ACTIVE

    def cost_per_gram(self):
        if self.landed_cost is None or not self.item.by_weight:
            return None
        return self.landed_cost / Decimal(1000)


class LotDocument(models.Model):
    class Kind(models.TextChoices):
        SPEC_SHEET = "spec_sheet", "Spec sheet"
        ALLERGEN_STATEMENT = "allergen_statement", "Allergen statement"
        ORIGIN = "origin", "Certificate of origin"
        ORGANIC = "organic", "Organic certificate"
        LAB_RESULT = "lab_result", "Lab result (heavy metals, pesticides)"
        OTHER = "other", "Other"

    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="documents")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    file = models.FileField(upload_to=document_path, storage=private_storage, validators=[validate_document_extension])
    description = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["lot", "kind", "pk"]

    def __str__(self):
        return f"{self.get_kind_display()} for {self.lot.code}"

    def get_absolute_url(self):
        return reverse("inventory:document", args=[self.pk])


class StockMovement(models.Model):
    """One change to a lot's quantity: positive in, negative out.  Rows are
    never changed or deleted; a mistake is corrected by another movement."""

    class Kind(models.TextChoices):
        RECEIPT = "receipt", "Received"
        BLEND_OUTPUT = "blend_output", "Made in a blend batch"
        BLEND_INPUT = "blend_input", "Used in a blend batch"
        SALE = "sale", "Packed for an order"
        ADJUSTMENT = "adjustment", "Adjustment"

    class Reason(models.TextChoices):
        COUNT = "count", "Stock count correction"
        SPOILED = "spoiled", "Spoiled or expired"
        DAMAGED = "damaged", "Damaged"
        SAMPLE = "sample", "Free sample (marketing)"
        MARKETING = "marketing", "Giveaway or other marketing use"
        PERSONAL = "personal", "Personal use"
        RETURNED = "returned", "Returned to stock"
        UNKNOWN = "unknown", "Unknown loss"
        OTHER = "other", "Other (say in the note)"

    # Reasons that are marketing expense, not loss.
    MARKETING_REASONS = (Reason.SAMPLE, Reason.MARKETING)

    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="movements")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    quantity = models.IntegerField(help_text="Positive adds to stock, negative removes it")
    reason = models.CharField(max_length=12, choices=Reason.choices, blank=True)
    reference = models.CharField(max_length=60, blank=True, db_index=True, help_text="Order number for packed orders")
    note = models.CharField(max_length=300, blank=True)
    blend_batch = models.ForeignKey(
        "BlendBatch", null=True, blank=True, on_delete=models.PROTECT, related_name="movements"
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(quantity=0),
                name="inventory_movement_nonzero",
                violation_error_message="The quantity can't be zero.",
            ),
            models.CheckConstraint(
                condition=Q(kind="adjustment", reason__gt="") | ~Q(kind="adjustment"),
                name="inventory_adjustment_has_reason",
                violation_error_message="An adjustment needs a reason.",
            ),
        ]

    def __str__(self):
        sign = "+" if self.quantity > 0 else ""
        return f"{self.lot.code} {sign}{self.lot.format_quantity(self.quantity)} {self.get_kind_display()}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AppendOnlyError("Stock movements cannot be changed; record a correcting adjustment")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AppendOnlyError("Stock movements cannot be deleted; record a correcting adjustment")


class StockAdjustment(StockMovement):
    """Stock movements of kind 'adjustment', for the admin's own page."""

    class Meta:
        proxy = True
        verbose_name = "stock adjustment"


class Recipe(models.Model):
    """How to make a blend, flavoured or herbal tea: the output item and the
    share of each ingredient by weight."""

    output_item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="recipes",
        limit_choices_to={"kind__in": [Item.Kind.TEA, Item.Kind.HERBAL]},
        help_text="The blend as a bulk item (e.g. 'Breakfast Blend')",
    )
    name = models.CharField(max_length=150, help_text="e.g. 'Breakfast Blend, 2026 recipe'")
    notes = models.TextField(blank=True, help_text="Method, mixing time, allergen handling")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def components_by_weight(self):
        return list(self.components.select_related("item").order_by("-grams_per_kg", "pk"))

    def total_grams_per_kg(self):
        return sum((c.grams_per_kg for c in self.components.all()), Decimal(0))


class RecipeComponent(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="components")
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="used_in_recipes",
        limit_choices_to={"kind__in": list(Item.BY_WEIGHT)},
    )
    grams_per_kg = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Grams of this per kg of blend; all components add up to 1000",
    )

    class Meta:
        ordering = ["recipe", "-grams_per_kg", "pk"]
        constraints = [models.UniqueConstraint(fields=["recipe", "item"], name="inventory_recipe_item_once")]

    def __str__(self):
        return f"{self.item}: {self.grams_per_kg} g/kg"


class BlendBatch(models.Model):
    """One batch of a recipe made here.  It uses specific ingredient lots
    and makes one new lot of the output item, so the blend can be traced
    back to each ingredient lot.  Made with services.make_blend()."""

    recipe = models.ForeignKey(Recipe, on_delete=models.PROTECT, related_name="batches")
    made_on = models.DateField(default=timezone.localdate)
    quantity_made = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Grams of blend made")
    best_by = models.DateField(
        null=True, blank=True, help_text="Leave blank for the earliest best-by date of the ingredient lots"
    )
    output_lot = models.OneToOneField(
        Lot, null=True, blank=True, on_delete=models.PROTECT, related_name="blend_batch", editable=False
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-made_on", "-pk"]
        verbose_name_plural = "blend batches"

    def __str__(self):
        lot = f" (lot {self.output_lot.code})" if self.output_lot_id else ""
        return f"{self.recipe} on {self.made_on:%Y-%m-%d}{lot}"


class BlendInput(models.Model):
    batch = models.ForeignKey(BlendBatch, on_delete=models.CASCADE, related_name="inputs")
    lot = models.ForeignKey(
        Lot, on_delete=models.PROTECT, related_name="used_in_batches", limit_choices_to={"item__kind__in": list(Item.BY_WEIGHT)}
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Grams used")

    class Meta:
        ordering = ["batch", "pk"]

    def __str__(self):
        return f"{self.lot.code}: {self.quantity:,} g"
