"""What the shop sells: products, their size options, and the bill of
materials for each size.

A tea is kept in bulk and weighed and packed when an order comes in, so a
size option is a recipe for one package, not stock: "Assam 50 g tin" is
50 g of Assam + 1 tin + 1 label.  Packing one (services.pack()) takes those
from inventory and records a SoldPackage, which ties the customer's order
to the tea lot for recalls and counts towards the organic sales limit.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.inventory.models import Item, Lot


class Product(models.Model):
    class Kind(models.TextChoices):
        TEA = "tea", "Tea or herbal tea, packed from bulk"
        GOODS = "goods", "Merchandise or accessory"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.TEA)
    tea = models.ForeignKey(
        Item,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="products",
        limit_choices_to={"kind__in": [Item.Kind.TEA, Item.Kind.HERBAL]},
        help_text="The bulk tea (or blend) packed for this product",
    )
    label_name = models.CharField(
        max_length=150,
        blank=True,
        help_text='The name on the label, saying what it is, e.g. "Assam black tea" or "Chamomile herbal tea"',
    )
    description = models.TextField(blank=True)
    sold_as_organic = models.BooleanField(
        default=False,
        help_text="Sold and described as organic.  Only organic lots can be packed for it, and its sales count "
        "towards the yearly limit for selling organic without certification.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.kind == self.Kind.TEA and not self.tea_id:
            raise ValidationError({"tea": "Choose the bulk tea this product is packed from."})
        if self.kind == self.Kind.GOODS:
            if self.tea_id:
                raise ValidationError({"tea": "Merchandise is not packed from bulk tea; leave this empty."})
            if self.sold_as_organic:
                raise ValidationError({"sold_as_organic": "Only teas can be sold as organic here."})


class SizeOption(models.Model):
    """One size a product is sold in, e.g. "50 g tin" or "25 g pouch".
    Expensive teas get smaller sizes; each tea has its own."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="size_options")
    name = models.CharField(max_length=60, help_text='As customers see it, e.g. "50 g tin"')
    sku = models.CharField(max_length=40, unique=True)
    net_grams = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Grams of tea in each package (teas only)",
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["product", "sort_order", "net_grams", "pk"]

    def __str__(self):
        return f"{self.product} {self.name}"

    def clean(self):
        if not self.product_id:
            return
        if self.product.kind == Product.Kind.TEA and not self.net_grams:
            raise ValidationError({"net_grams": "Say how many grams of tea go in each package."})
        if self.product.kind == Product.Kind.GOODS and self.net_grams:
            raise ValidationError({"net_grams": "Only teas have a net weight here; leave this empty."})

    def bill_of_materials(self):
        """[(item, quantity)] that one package uses: the tea first (grams),
        then each packaging or merchandise line (pieces)."""
        lines = []
        if self.product.tea_id and self.net_grams:
            lines.append((self.product.tea, self.net_grams))
        lines += [(line.item, line.quantity) for line in self.bom_lines.select_related("item")]
        return lines

    def tea_lots(self):
        """Lots this size can be packed from, oldest best-by first: usable
        lots of the product's tea, and only organic ones if it is sold as
        organic."""
        lots = self.product.tea.usable_lots()
        return lots.filter(organic=True) if self.product.sold_as_organic else lots

    def packages_available(self):
        """How many packages can be packed from usable stock now.  Tea
        counts whole packages per lot, since a package comes from one lot."""
        counts = []
        if self.product.tea_id and self.net_grams:
            counts.append(sum(lot.quantity_on_hand // self.net_grams for lot in self.tea_lots()))
        for line in self.bom_lines.select_related("item"):
            counts.append(line.item.on_hand() // line.quantity)
        return min(counts) if counts else 0


class BomLine(models.Model):
    """A piece one package of a size option uses besides the tea: the tin
    or pouch, the label, a scoop, or the merchandise item itself."""

    size_option = models.ForeignKey(SizeOption, on_delete=models.CASCADE, related_name="bom_lines")
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="bom_lines",
        limit_choices_to={"kind__in": [k for k in Item.Kind.values if k not in Item.BY_WEIGHT]},
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["size_option", "pk"]
        verbose_name = "bill of materials line"
        constraints = [models.UniqueConstraint(fields=["size_option", "item"], name="catalog_bom_item_once")]

    def __str__(self):
        return f"{self.quantity} × {self.item}"

    def clean(self):
        if self.item_id and self.item.by_weight:
            raise ValidationError({"item": "Bulk items go in by weight: the tea is the product's, set by net grams."})


class SoldPackage(models.Model):
    """One package packed for a customer order: which lot its tea came
    from (the label's lot code), and what it sold for."""

    size_option = models.ForeignKey(SizeOption, on_delete=models.PROTECT, related_name="sold_packages")
    order_reference = models.CharField(max_length=60, db_index=True)
    tea_lot = models.ForeignKey(Lot, null=True, blank=True, on_delete=models.PROTECT, related_name="sold_packages")
    tea_grams = models.PositiveIntegerField(null=True, blank=True, help_text="Grams actually packed")
    amount = models.DecimalField(max_digits=8, decimal_places=2, help_text="What the customer paid for this package")
    organic = models.BooleanField(default=False, help_text="Sold as organic")
    packed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-packed_at", "-pk"]

    def __str__(self):
        lot = f" from lot {self.tea_lot.code}" if self.tea_lot_id else ""
        return f"{self.size_option} for order {self.order_reference}{lot}"
