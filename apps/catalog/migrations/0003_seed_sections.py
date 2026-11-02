"""The shop's standard sections, so its navigation exists from the start.
The owner renames, reorders, hides or adds to them in the admin."""

from django.db import migrations

CATEGORIES = [
    # (slug, name, section, herbal, motif, palette, intro)
    ("black", "Black tea", "tea", False, "leaf", "bark",
     "Fully oxidised leaves that brew a deep amber cup, from brisk and malty to smooth and honeyed."),
    ("green", "Green tea", "tea", False, "sprig", "moss",
     "Leaves heated soon after picking to keep them green: grassy, sweet, toasty or marine."),
    ("oolong", "Oolong", "tea", False, "blossom", "cornflower",
     "Partly oxidised teas between green and black, often rolled or twisted, often floral or roasted."),
    ("white", "White tea", "tea", False, "butterfly", "buttercup",
     "Buds and young leaves, simply withered and dried, with a delicate, sweet cup."),
    ("dark", "Pu-erh and dark tea", "tea", False, "fern", "bark",
     "Teas aged or fermented after processing, earthy and smooth."),
    ("flavoured", "Flavoured tea and blends", "tea", False, "bee", "poppy",
     "Tea blended with fruit, flowers, spices or flavourings."),
    ("herbal", "Herbal teas and tisanes", "tea", True, "blossom", "plum",
     "Infusions of flowers, leaves, roots and fruit, not from the tea plant."),
    ("teaware", "Teapots and teaware", "goods", False, "teapot", "cornflower",
     "Pots, cups and the things that make brewing easy."),
    ("accessories", "Brewing accessories", "goods", False, "sprig", "moss",
     "Strainers, scoops, tins and filters."),
    ("merch", "Shop goods", "goods", False, "bird", "poppy",
     "Our own goods, with the shop's designs."),
]

COLLECTIONS = [
    ("specials", "Specials", "poppy", "bee", "Teas at a special price for a while."),
    ("this-weeks-picks", "This week's picks", "buttercup", "bird", "What we are drinking and enjoying this week."),
    ("new-arrivals", "New arrivals", "moss", "sprig", "Teas just in."),
]


def seed(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Collection = apps.get_model("catalog", "Collection")
    for order, (slug, name, section, herbal, motif, palette, intro) in enumerate(CATEGORIES):
        Category.objects.get_or_create(
            slug=slug,
            defaults=dict(name=name, section=section, is_herbal=herbal, motif=motif, palette=palette, intro=intro,
                          sort_order=order * 10),
        )
    for order, (slug, name, palette, motif, intro) in enumerate(COLLECTIONS):
        Collection.objects.get_or_create(
            slug=slug,
            defaults=dict(name=name, palette=palette, motif=motif, intro=intro, sort_order=order * 10, featured=True),
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_storefront_fields")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
