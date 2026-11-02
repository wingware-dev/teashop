"""What the shop sells: products, their size options, and the bill of
materials for each size.

A tea is kept in bulk and weighed and packed when an order comes in, so a
size option is a recipe for one package, not stock: "Assam 50 g tin" is
50 g of Assam + 1 tin + 1 label.  Packing one (services.pack()) takes those
from inventory and records a SoldPackage, which ties the customer's order
to the tea lot for recalls and counts towards the organic sales limit.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.design import MOTIFS, PALETTES
from apps.inventory.models import Item, Lot

from . import copy_rules


def _copy_errors(obj, fields):
    """{field: [health claim problems]} for the named text fields."""
    errors = {}
    for name in fields:
        problems = copy_rules.health_claim_problems(getattr(obj, name), where=obj._meta.get_field(name).verbose_name.capitalize())
        if problems:
            errors[name] = problems
    return errors


class StorefrontSection(models.Model):
    """What category, region and collection pages share: a name, a short
    introduction, and the motif and palette the page is drawn with."""

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True)
    intro = models.TextField(blank=True, help_text="A few sentences at the top of the page; no health claims")
    motif = models.CharField(max_length=20, choices=MOTIFS, default="leaf")
    palette = models.CharField(max_length=20, choices=PALETTES, default="moss")
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, help_text="Shown in the shop")

    class Meta:
        abstract = True
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        errors = _copy_errors(self, ["name", "intro"])
        if errors:
            raise ValidationError(errors)


class Category(StorefrontSection):
    """A shop section by kind: black, green, oolong, flavoured, herbal
    tea; merch; accessories."""

    class Section(models.TextChoices):
        TEA = "tea", "Teas"
        GOODS = "goods", "Merch and accessories"

    section = models.CharField(max_length=8, choices=Section.choices, default=Section.TEA)
    is_herbal = models.BooleanField(
        default=False,
        help_text='Herbal teas (not from the tea plant): product names must say "herbal tea" or "tisane"',
    )

    class Meta(StorefrontSection.Meta):
        verbose_name_plural = "categories"

    def get_absolute_url(self):
        name = "storefront:category" if self.section == self.Section.TEA else "storefront:goods_category"
        return reverse(name, args=[self.slug])


class Region(StorefrontSection):
    """Where teas are grown: Assam, Yunnan, Uji, Nuwara Eliya..."""

    country = models.CharField(max_length=80, help_text="Country, for grouping the regions list")

    class Meta(StorefrontSection.Meta):
        ordering = ["country", "sort_order", "name"]

    def get_absolute_url(self):
        return reverse("storefront:region", args=[self.slug])


class CollectionQuerySet(models.QuerySet):
    def showing(self, day=None):
        """Active collections whose dates (if any) include day (default today)."""
        day = day or timezone.localdate()
        return self.filter(is_active=True).exclude(starts_on__gt=day).exclude(ends_on__lt=day)


class Collection(StorefrontSection):
    """A hand-picked list: specials, this week's picks, new arrivals."""

    products = models.ManyToManyField("Product", blank=True, related_name="collections")
    starts_on = models.DateField(null=True, blank=True, help_text="Shown from this day (empty: now)")
    ends_on = models.DateField(null=True, blank=True, help_text="Shown up to and including this day (empty: no end)")
    featured = models.BooleanField(default=False, help_text="Shown on the home page")

    objects = CollectionQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse("storefront:collection", args=[self.slug])

    def clean(self):
        super().clean()
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValidationError({"ends_on": "The end date is before the start date."})


class FlavourNote(models.Model):
    """A tasting note customers can filter by: malty, floral, citrus..."""

    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        errors = _copy_errors(self, ["name"])
        if errors:
            raise ValidationError(errors)


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

    # -- What the shop shows ---------------------------------------------
    class Caffeine(models.TextChoices):
        NONE = "none", "None (caffeine-free)"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.PROTECT, related_name="products")
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    summary = models.CharField(
        max_length=200, blank=True, help_text="One line for lists and search results, and the page description"
    )
    origin_detail = models.CharField(
        max_length=200, blank=True, help_text='Where exactly, e.g. "Second flush, Halmari estate, upper Assam"'
    )
    origin_certified = models.BooleanField(
        default=False,
        help_text="Certified genuine for a protected origin name such as Darjeeling (keep the certificate with "
        "the lot).  Only then can the name and copy use that origin.",
    )
    tasting_notes = models.TextField(blank=True, help_text="Taste, aroma, colour of the cup")
    flavour_notes = models.ManyToManyField(FlavourNote, blank=True, related_name="products")
    caffeine = models.CharField(max_length=8, choices=Caffeine.choices, blank=True)
    brew_temp_c = models.PositiveSmallIntegerField(
        "water temperature (°C)", null=True, blank=True, validators=[MinValueValidator(40), MaxValueValidator(100)]
    )
    brew_minutes = models.CharField(
        "steeping time", max_length=30, blank=True, help_text='e.g. "3-4 minutes"'
    )
    brew_grams = models.DecimalField(
        "tea per cup (g)", max_digits=4, decimal_places=1, null=True, blank=True,
        help_text="Grams for a 250 ml (8 oz) cup",
    )
    brew_infusions = models.PositiveSmallIntegerField(
        "infusions", null=True, blank=True, help_text="How many times the leaves can be steeped"
    )
    brew_notes = models.TextField("brewing notes", blank=True, help_text="Anything else: iced, with milk, gongfu style")
    featured = models.BooleanField(default=False, help_text="Shown on the home page")

    TEXT_FIELDS = ["name", "label_name", "summary", "origin_detail", "description", "tasting_notes", "brew_notes"]

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("storefront:product", args=[self.slug])

    @property
    def is_herbal(self):
        """A herbal tea (not from the tea plant): its tea is a herbal
        ingredient, or it is in a herbal category."""
        return bool((self.tea_id and self.tea.kind == Item.Kind.HERBAL) or (self.category_id and self.category.is_herbal))

    def copy_problems(self):
        """{field: [problems]} with the words customers see: health claims,
        herbal naming, caffeine-free, protected origins."""
        errors = _copy_errors(self, self.TEXT_FIELDS)

        def add(field, problems):
            if problems:
                errors.setdefault(field, []).extend(problems)

        if self.is_herbal:
            add("name", copy_rules.herbal_name_problems(self.name))
            if self.label_name:
                add("label_name", copy_rules.herbal_name_problems(self.label_name))
        for name in self.TEXT_FIELDS:
            where = self._meta.get_field(name).verbose_name.capitalize()
            add(name, copy_rules.caffeine_free_problems(getattr(self, name), self.caffeine == self.Caffeine.NONE, where))
            add(name, copy_rules.origin_problems(getattr(self, name), self.origin_certified, where))
        return errors

    def clean(self):
        if self.kind == self.Kind.TEA and not self.tea_id:
            raise ValidationError({"tea": "Choose the bulk tea this product is packed from."})
        if self.kind == self.Kind.GOODS:
            if self.tea_id:
                raise ValidationError({"tea": "Merchandise is not packed from bulk tea; leave this empty."})
            if self.sold_as_organic:
                raise ValidationError({"sold_as_organic": "Only teas can be sold as organic here."})
        if self.category_id:
            wanted = Category.Section.TEA if self.kind == self.Kind.TEA else Category.Section.GOODS
            if self.category.section != wanted:
                raise ValidationError({"category": f"Choose a category in {Category.Section(wanted).label}."})
        errors = self.copy_problems()
        if errors:
            raise ValidationError(errors)

    # -- Facts for the product page ----------------------------------------
    def shop_sizes(self):
        """Active sizes, smallest first."""
        return [size for size in self.size_options.all() if size.is_active]

    def from_price(self):
        prices = [size.price for size in self.shop_sizes()]
        return min(prices) if prices else None

    def shop_facts(self):
        """What the tea in the packages being sold now contains, from the
        usable lots it is packed from: countries grown in, the ingredient
        list, and every allergen any of those lots declares (so a package
        from any of them is covered).  None for merchandise."""
        if self.kind != self.Kind.TEA or not self.tea_id:
            return None
        lots = list(self.tea.usable_lots().prefetch_related("allergens"))
        if self.sold_as_organic:
            lots = [lot for lot in lots if lot.organic]
        countries, allergens = [], []
        for lot in lots:
            for country in lot.country_of_origin.split(","):
                if country.strip() and country.strip() not in countries:
                    countries.append(country.strip())
            for allergen in lot.allergens.all():
                if allergen.name not in allergens:
                    allergens.append(allergen.name)
        ingredients = (lots[0].ingredients if lots else "") or self.tea.ingredient_name
        return {"countries": countries, "ingredients": ingredients, "allergens": allergens, "has_stock": bool(lots)}


def photo_path(photo, filename):
    return f"products/{photo.product.slug}/{filename}"


class ProductPhoto(models.Model):
    """The owner's own photo of a product.  AI-made art may decorate pages
    but never stands in for what the customer is buying.

    On save the upload is turned upright, stripped of its metadata
    (phones record where a photo was taken, which would be the owner's
    home) and limited in size, and smaller copies for phones are made
    (see images.py)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to=photo_path, width_field="width", height_field="height")
    width = models.PositiveIntegerField(editable=False, default=0)
    height = models.PositiveIntegerField(editable=False, default=0)
    alt_text = models.CharField(
        max_length=200,
        help_text='What the photo shows, for people who cannot see it, e.g. "Twisted dark leaves in an open tin"',
    )
    sort_order = models.PositiveSmallIntegerField(default=0, help_text="The first photo is the main one")

    class Meta:
        ordering = ["product", "sort_order", "pk"]

    def __str__(self):
        return f"{self.product}: {self.alt_text}"

    def clean(self):
        if not self.alt_text.strip():
            raise ValidationError({"alt_text": "Describe the photo for people who cannot see it."})

    def save(self, *args, **kwargs):
        from . import images

        if self.image and not getattr(self.image, "_committed", True):
            images.clean_upload(self)
        super().save(*args, **kwargs)
        images.make_renditions(self)

    def delete(self, *args, **kwargs):
        from . import images

        images.delete_renditions(self)
        storage, name = self.image.storage, self.image.name
        result = super().delete(*args, **kwargs)
        if name:
            storage.delete(name)
        return result

    def srcset(self):
        from . import images

        return images.srcset(self)

    def url_for_width(self, width):
        from . import images

        return images.rendition_url(self, width)

    @property
    def small_url(self):
        """For cards and thumbnails (480 pixels wide, or the photo)."""
        return self.url_for_width(480)


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

    class Package(models.TextChoices):
        TIN = "tin", "Tin"
        POUCH = "pouch", "Pouch"
        BOX = "box", "Box"

    package = models.CharField(
        max_length=8, choices=Package.choices, blank=True, help_text="For the shop's package filter (teas)"
    )
    shipping_grams = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Weight of one packed package, for shipping rates.  Empty: the tea plus a usual weight for its "
        "package (teas), or a usual weight for merchandise.  Weigh one to set it exactly.",
    )
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

    def shipping_weight(self):
        """Grams one packed package weighs, for shipping rates: as set, or
        estimated from the tea and its package (settings.SHIPPING_PACKAGE_GRAMS,
        SHIPPING_DEFAULT_ITEM_GRAMS)."""
        from django.conf import settings

        if self.shipping_grams:
            return self.shipping_grams
        if self.net_grams:
            return self.net_grams + settings.SHIPPING_PACKAGE_GRAMS.get(self.package, 30)
        return settings.SHIPPING_DEFAULT_ITEM_GRAMS

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
