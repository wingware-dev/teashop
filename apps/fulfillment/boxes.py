"""Suggesting the box for a parcel from its packages' sizes and weight.

The smallest box in stock that holds every package with room for filler
(settings.BOX_FILL_FACTOR) and whose longest sides take the biggest
package.  The owner can always choose another box, or one not on the list.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .models import BoxSize


@dataclass
class Suggestion:
    box: BoxSize = None
    volume: Decimal = Decimal(0)  # cubic inches the packages need, with filler room
    grams: int = 0  # packages only
    biggest: list = field(default_factory=list)  # the biggest package's sides, longest first
    note: str = ""
    # Boxes that hold it, smallest first (the suggestion is the first in stock).
    fitting: list = field(default_factory=list)

    def parcel_grams(self, box=None):
        """Estimated parcel weight with box (default the suggested one)."""
        box = box or self.box
        return self.grams + (box.empty_grams if box else settings.SHIPPING_BOX_GRAMS)


def package_dimensions(size):
    """(length, width, height) in inches of one packed package of size,
    longest first."""
    try:
        own = size.dimensions
    except ObjectDoesNotExist:
        own = None
    if own is not None:
        sides = [own.length_in, own.width_in, own.height_in]
    else:
        usual = settings.PACKAGE_DIMENSIONS_IN
        kind = size.package if size.product.kind == "tea" else ""
        sides = [Decimal(str(side)) for side in usual.get(kind, usual[""])]
    return sorted(sides, reverse=True)


def holds(box, biggest, volume, grams):
    if any(side < need for side, need in zip(box.dimensions, biggest)):
        return False
    if box.volume < volume:
        return False
    return box.max_grams is None or grams + box.empty_grams <= box.max_grams


def suggest(size_quantities, boxes=None):
    """The Suggestion for packages [(size_option, quantity)]."""
    result = Suggestion()
    volume = Decimal(0)
    for size, quantity in size_quantities:
        if not quantity:
            continue
        sides = package_dimensions(size)
        volume += sides[0] * sides[1] * sides[2] * quantity
        result.grams += size.shipping_weight() * quantity
        if sides > result.biggest:
            result.biggest = sides
    if not result.biggest:
        result.note = "Nothing to ship yet."
        return result
    result.volume = (volume * Decimal(str(settings.BOX_FILL_FACTOR))).quantize(Decimal("0.1"))
    candidates = boxes if boxes is not None else BoxSize.objects.filter(is_active=True).select_related("item")
    result.fitting = sorted((box for box in candidates if holds(box, result.biggest, result.volume, result.grams)),
                            key=lambda box: (box.volume, box.pk))
    in_stock = [box for box in result.fitting if box.in_stock()]
    if in_stock:
        result.box = in_stock[0]
        result.note = (f"The smallest box in stock that holds {result.volume:f} cubic inches "
                       f"and the biggest package ({_sides(result.biggest)}).")
    elif result.fitting:
        result.box = result.fitting[0]
        result.note = "No box that fits is in stock: use another box, or restock this one."
    else:
        result.note = (f"No box on your list holds it all ({result.volume:f} cubic inches, biggest package "
                       f"{_sides(result.biggest)}): use a bigger box, or ship part now and the rest later.")
    return result


def _sides(sides):
    return " × ".join(f"{side.normalize():f}" for side in sides) + " in"
