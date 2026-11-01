"""Packing packages for orders, label facts, and organic sales.

The fulfillment phase calls pack() once per package as it weighs and
packs an order, then prints label_for(package).
"""

from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.inventory import services as inventory
from apps.inventory.models import StockMovement

from .models import Product, SoldPackage

GRAMS_PER_OUNCE = Decimal("28.349523125")


def pack(size_option, order_reference, *, amount=None, lot=None, tea_grams=None):
    """Take one package's bill of materials from stock for an order and
    record it as a SoldPackage.

    - The tea comes from one lot: lot if given, else the usable lot with
      the earliest best-by date that holds a whole package (organic lots
      only for a product sold as organic).
    - tea_grams is what the scale showed, at least the net weight; it
      defaults to the net weight.
    - Packaging comes from its lots, oldest first.
    - amount is what the customer paid; it defaults to the size's price.

    Raises inventory.StockError when something is short; then nothing is
    taken.
    """
    if not order_reference:
        raise ValueError("A packed package needs its order reference")
    product = size_option.product
    amount = size_option.price if amount is None else Decimal(amount)
    with transaction.atomic():
        tea_lot = None
        if product.kind == Product.Kind.TEA:
            net = size_option.net_grams
            tea_grams = net if tea_grams is None else int(tea_grams)
            if tea_grams < net:
                raise inventory.StockError(
                    f"{tea_grams} g is under the labelled net weight of {net} g; add tea before packing."
                )
            if lot is None:
                tea_lot = inventory.pick_lot(product.tea, tea_grams, lots=size_option.tea_lots())
            else:
                tea_lot = lot
                if lot.item_id != product.tea_id:
                    raise inventory.StockError(f"Lot {lot.code} is {lot.item}, not {product.tea}.")
                if product.sold_as_organic and not lot.organic:
                    raise inventory.StockError(f"{product} is sold as organic; lot {lot.code} is not organic.")
            inventory.post_movement(tea_lot, -tea_grams, StockMovement.Kind.SALE, reference=order_reference)
        else:
            tea_grams = None
        for line in size_option.bom_lines.select_related("item"):
            inventory.consume(line.item, line.quantity, reference=order_reference)
        return SoldPackage.objects.create(
            size_option=size_option,
            order_reference=order_reference,
            tea_lot=tea_lot,
            tea_grams=tea_grams,
            amount=amount,
            organic=product.sold_as_organic,
        )


def ounces(grams):
    """Net weight in ounces to two places, rounded down so the label never
    claims more than is in the package."""
    return (Decimal(grams) / GRAMS_PER_OUNCE).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def net_weight_text(grams):
    return f"Net wt {ounces(grams)} oz ({grams} g)"


def join_words(words):
    words = list(words)
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


@dataclass
class Label:
    """The facts printed on one package's label."""

    name: str
    net_weight: str
    grown_in: str
    ingredients: str
    allergens: list
    lot_code: str
    best_by: object
    packer: str
    # Facts missing for a legal label; print nothing until they are fixed.
    problems: list = field(default_factory=list)

    @property
    def contains(self):
        return f"Contains: {join_words(self.allergens)}" if self.allergens else ""


def label_data(size_option, lot):
    """Label facts for a package of size_option packed from lot."""
    product = size_option.product
    if product.kind != Product.Kind.TEA:
        raise ValueError(f"{product} is not packed from bulk, so has no package label")
    countries = [c.strip() for c in lot.country_of_origin.split(",") if c.strip()]
    label = Label(
        name=product.label_name or product.name,
        net_weight=net_weight_text(size_option.net_grams),
        grown_in=f"Grown in {join_words(countries)}" if countries else "",
        ingredients=lot.ingredients or product.tea.ingredient_name,
        allergens=[a.name for a in lot.allergens.all()],
        lot_code=lot.code,
        best_by=lot.best_by,
        packer=settings.LABEL_PACKER_ADDRESS,
    )
    if not label.grown_in and product.tea.kind in product.tea.GROWN:
        label.problems.append(f'Lot {lot.code} has no country of origin for "Grown in".')
    if not label.best_by:
        label.problems.append(f"Lot {lot.code} has no best-by date.")
    if not label.ingredients:
        label.problems.append(f"No ingredient wording for {product.tea} or lot {lot.code}.")
    if not label.packer:
        label.problems.append("The packer's name and address (LABEL_PACKER_ADDRESS) is not set.")
    return label


def label_for(package):
    return label_data(package.size_option, package.tea_lot)


def organic_sales(year=None):
    """Sales of packages sold as organic in a calendar year (default: this
    year), for the limit on selling organic without certification."""
    year = year or timezone.localdate().year
    total = SoldPackage.objects.filter(organic=True, packed_at__year=year).aggregate(total=Sum("amount"))["total"]
    return total or Decimal("0.00")
