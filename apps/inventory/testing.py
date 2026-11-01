"""Builders for tests that need stock (used by inventory and catalog tests)."""

from datetime import date

from .models import Allergen, Item, Lot, Recipe, RecipeComponent, Supplier


def make_supplier(name="Leaf Importers"):
    return Supplier.objects.get_or_create(name=name)[0]


def make_item(name="Assam", code=None, kind=Item.Kind.TEA, **fields):
    fields.setdefault("ingredient_name", "black tea" if kind == Item.Kind.TEA else name.lower())
    return Item.objects.create(name=name, code=code or name.upper().replace(" ", "-")[:20], kind=kind, **fields)


def make_lot(item, quantity=1000, best_by=date(2028, 1, 1), country="India", supplier=None, allergens=(), **fields):
    if item.by_weight:
        fields.setdefault("best_by", best_by)
        fields.setdefault("country_of_origin", country if item.kind in Item.GROWN else "")
    lot = Lot.objects.create(item=item, quantity_received=quantity, supplier=supplier, **fields)
    if allergens:
        lot.allergens.set(Allergen.objects.filter(code__in=allergens))
    return lot


def make_recipe(output_item, parts):
    """parts: [(item, grams_per_kg)]."""
    recipe = Recipe.objects.create(output_item=output_item, name=f"{output_item.name} recipe")
    for item, grams in parts:
        RecipeComponent.objects.create(recipe=recipe, item=item, grams_per_kg=grams)
    return recipe
