"""A small made-up catalog to try the shop with on a laptop, and for the
browser tests and milestone screenshots: teas of each kind with stock,
regions, collections, merch, tea notes and two page designs.

Load it with ``python manage.py load_demo_catalog`` (refused in
production).  Every name, garden and price here is invented for the
demo; none of it is meant to go live.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import BomLine, Category, Collection, FlavourNote, Product, Region, SizeOption
from apps.inventory.models import Allergen, Item, Lot, Supplier

from .models import Article, PageVariant

REGIONS = [
    # slug, name, country, motif, palette, intro
    ("assam", "Assam", "India", "leaf", "bark",
     "The low, hot Brahmaputra valley, where the tea plant's broad-leaved Assam variety makes strong, malty black teas."),
    ("darjeeling", "Darjeeling", "India", "bird", "moss",
     "Steep gardens in the Himalayan foothills, picked in flushes from spring to autumn."),
    ("yunnan", "Yunnan", "China", "butterfly", "buttercup",
     "China's south-western mountains, home of golden-tipped black teas and of pu-erh."),
    ("fujian", "Fujian", "China", "blossom", "plum",
     "The coastal province where white tea and many oolongs began."),
    ("shizuoka", "Shizuoka", "Japan", "fern", "moss",
     "Japan's largest tea region, between Mount Fuji and the sea, known for steamed sencha."),
    ("nantou", "Nantou", "Taiwan", "bee", "cornflower",
     "Taiwan's mountainous heart, where rolled oolongs are grown and roasted."),
]

NOTES = ["Malty", "Honey", "Cocoa", "Grassy", "Marine", "Roasted", "Floral", "Citrus", "Vanilla", "Nutty",
         "Tart", "Berry", "Apple", "Brisk"]

TEAS = [
    # slug, name, category, region, item kind, ingredients, countries, allergens, caffeine, notes,
    # (temp, minutes, grams, infusions), sizes [(grams, package, price)], extras
    dict(slug="assam-second-flush", name="Assam Second Flush", category="black", region="assam",
         ingredients="black tea", countries="India", caffeine="high", notes=["Malty", "Honey", "Brisk"],
         brew=(95, "3-4 minutes", "2.5", 2), sizes=[(50, "pouch", "9.00"), (100, "tin", "16.00")],
         summary="A full, malty black tea with a honeyed finish; takes milk well.",
         origin_detail="Summer (second flush) picking, upper Assam",
         tasting_notes="Deep copper cup with a malty body, a hint of dried fruit and a long, honeyed finish.",
         description="Second-flush Assam is picked in early summer, when the leaves are at their richest. "
                     "This one brews a bold cup that stands up to milk and sugar, and is just as good plain.",
         brew_notes="For a stronger breakfast cup, use 3 g and steep the full 4 minutes.",
         featured=True, collections=["this-weeks-picks"]),
    dict(slug="darjeeling-first-flush", name="Darjeeling First Flush", category="black", region="darjeeling",
         ingredients="black tea", countries="India", caffeine="medium", notes=["Floral", "Citrus"],
         brew=(90, "2-3 minutes", "2", 2), sizes=[(25, "pouch", "11.00"), (50, "tin", "20.00")],
         summary="Light, bright and flowery: the first picking of the spring.",
         origin_detail="Spring (first flush) picking", origin_certified=True,
         tasting_notes="Pale gold and lively, with notes of spring flowers and a gentle, crisp finish.",
         description="The first flush is the year's first picking in the Darjeeling hills, after the plants' winter "
                     "rest. It is lightly oxidised, so it drinks closer to a green tea than a breakfast blend.",
         collections=["new-arrivals"]),
    dict(slug="yunnan-golden-buds", name="Yunnan Golden Buds", category="black", region="yunnan",
         ingredients="black tea", countries="China", caffeine="medium", notes=["Cocoa", "Honey"],
         brew=(90, "3 minutes", "2.5", 3), sizes=[(25, "pouch", "8.00"), (50, "tin", "14.50")],
         summary="Downy golden buds that brew smooth and sweet, with a note of cocoa.",
         tasting_notes="Smooth and round, with cocoa, baked sweet potato and a soft honey sweetness.",
         description="Made almost entirely from buds, which turn gold as they are rolled and dried.",
         featured=True, collections=["new-arrivals"]),
    dict(slug="sencha-morning-mist", name="Sencha Morning Mist", category="green", region="shizuoka",
         ingredients="green tea", countries="Japan", caffeine="medium", notes=["Grassy", "Marine"],
         brew=(75, "1-2 minutes", "3", 3), sizes=[(50, "pouch", "12.00"), (100, "tin", "22.00")],
         summary="A bright, steamed green tea: fresh-cut grass and a savoury sea-breeze note.",
         tasting_notes="Vivid green cup, sweet and grassy, with a savoury, marine depth.",
         description="Sencha leaves are steamed within hours of picking to keep their colour and freshness.",
         brew_notes="Water that is too hot makes green tea bitter: let boiled water cool for a few minutes.",
         featured=True, collections=["this-weeks-picks"]),
    dict(slug="dong-ding-oolong", name="Dong Ding Oolong", category="oolong", region="nantou",
         ingredients="oolong tea", countries="Taiwan", caffeine="medium", notes=["Roasted", "Floral", "Honey"],
         brew=(95, "1 minute, longer each time", "5", 5), sizes=[(50, "pouch", "15.00")],
         summary="Rolled and gently roasted: toasty, floral and long-lasting.",
         tasting_notes="Golden cup with toasted grain, orchid and a lingering, honeyed sweetness.",
         description="Rolled into tight balls and roasted over charcoal, which gives its warm, toasty edge.",
         brew_notes="Brew it gongfu style: lots of leaf, short steeps, many infusions.",
         collections=["specials"]),
    dict(slug="silver-needle", name="Silver Needle", category="white", region="fujian",
         ingredients="white tea", countries="China", caffeine="low", notes=["Honey", "Floral"],
         brew=(80, "4-5 minutes", "3", 3), sizes=[(25, "tin", "13.00")],
         summary="Silvery buds with a delicate, sweet, honeyed cup.",
         tasting_notes="Very pale and silky, with honeydew, hay and a whisper of flowers.",
         description="Only the unopened buds are picked, then simply withered and dried.",
         featured=True, collections=["specials"]),
    dict(slug="earl-grey-cornflower", name="Earl Grey with Cornflower", category="flavoured", region="",
         ingredients="black tea, natural bergamot flavour, cornflower petals", countries="India, Sri Lanka",
         caffeine="high", notes=["Citrus", "Floral", "Brisk"], brew=(95, "3-4 minutes", "2.5", 1),
         sizes=[(50, "pouch", "9.50"), (100, "tin", "17.00")],
         summary="Black tea with bergamot and blue cornflower petals.",
         tasting_notes="Brisk black tea lifted by bright bergamot citrus.",
         collections=["this-weeks-picks"]),
    dict(slug="vanilla-almond-black", name="Vanilla Almond Black", category="flavoured", region="",
         ingredients="black tea, almond pieces, natural vanilla flavour", countries="India",
         allergens=["tree-nuts"], caffeine="high", notes=["Vanilla", "Nutty"],
         brew=(95, "4 minutes", "3", 1), sizes=[(50, "pouch", "10.00")],
         summary="Black tea with almond pieces and vanilla: dessert in a cup.",
         tasting_notes="Creamy vanilla and toasted almond over a smooth black tea.",
         collections=["specials"]),
    dict(slug="chamomile-meadow", name="Chamomile Meadow Herbal Tea", category="herbal", region="",
         kind="herbal", ingredients="chamomile flowers", countries="Egypt", caffeine="none",
         notes=["Honey", "Apple", "Floral"], brew=(100, "5 minutes", "2", 1), sizes=[(30, "pouch", "8.00")],
         summary="Whole chamomile flowers: mellow, honeyed and naturally caffeine-free.",
         tasting_notes="Golden and mellow, with honey and baked apple.",
         featured=True),
    dict(slug="hibiscus-berry-tisane", name="Hibiscus Berry Tisane", category="herbal", region="",
         kind="herbal", ingredients="hibiscus, apple pieces, elderberries, natural berry flavour",
         countries="Egypt, Germany", caffeine="none", notes=["Tart", "Berry"], brew=(100, "6-8 minutes", "3", 1),
         sizes=[(50, "pouch", "8.50")],
         summary="Ruby-red, tart and fruity; lovely iced.",
         tasting_notes="Deep red cup, tangy hibiscus with ripe berries.",
         brew_notes="For iced tea, brew double strength and pour over ice.",
         collections=["new-arrivals"]),
]

GOODS = [
    dict(slug="glass-teapot", name="Glass Teapot, 600 ml", category="teaware", price="28.00", kind="accessory",
         summary="Heat-proof glass with a removable stainless steel infuser.",
         description="Watch the leaves unfurl. Holds about three cups."),
    dict(slug="fine-mesh-strainer", name="Fine Mesh Strainer", category="accessories", price="8.00",
         kind="accessory", summary="Rests on a cup or pot; fine enough for rooibos and broken leaf.",
         description="Stainless steel, with a drip tray."),
    dict(slug="bee-blossom-tea-towel", name="Bee and Blossom Tea Towel", category="merch", price="14.00",
         kind="merch", summary="Cotton tea towel printed with the shop's bees and blossoms.",
         description="100% cotton, 50 × 70 cm."),
]

ARTICLES = [
    dict(slug="how-black-tea-gets-its-colour", title="How black tea gets its colour", motif="leaf", palette="bark",
         summary="Green, oolong and black teas can come from the same plant. What changes is oxidation.",
         body="Every true tea comes from one plant, Camellia sinensis. Whether a leaf becomes green, oolong or "
              "black tea depends mostly on what happens after it is picked.\n\n"
              "## Withering and rolling\n\n"
              "Fresh leaves are spread out to wither and soften, then rolled. Rolling breaks the leaf's cells "
              "and lets the air reach the juices inside.\n\n"
              "## Oxidation\n\n"
              "Exposed to air, the leaf darkens, much as a cut apple turns brown. Black tea is left to oxidise "
              "fully, which brings its copper colour and deep, malty flavours. Green tea is heated soon after "
              "picking to stop oxidation, and oolong sits somewhere between.",
         products=["assam-second-flush", "yunnan-golden-buds"], days_ago=3),
    dict(slug="brewing-green-tea", title="Brewing green tea that isn't bitter", motif="sprig", palette="moss",
         summary="Cooler water and shorter steeps bring out green tea's sweetness.",
         body="Most bitter green tea is simply brewed too hot or too long.\n\n"
              "## Let the water cool\n\n"
              "Boiling water scalds delicate green leaves. Let it stand for a few minutes, to around 75 to 80 °C.\n\n"
              "## Steep briefly, then again\n\n"
              "One to two minutes is plenty. Good green tea gives two or three infusions, each a little different.",
         products=["sencha-morning-mist"], days_ago=10),
    dict(slug="teas-long-road-west", title="Tea's long road west", motif="bird", palette="cornflower",
         summary="From Chinese tea houses to European parlours: how tea travelled the world.",
         body="Tea was drunk in China for many centuries before it reached Europe.\n\n"
              "Dutch traders brought some of the first tea to Europe early in the 1600s, and within a few "
              "decades it was being sold in London's coffee houses. Tea gardens followed in India and Ceylon "
              "in the 1800s, and with them the strong black teas many people now think of simply as tea.",
         products=["darjeeling-first-flush"], days_ago=20),
]

VARIANTS = [
    dict(product="assam-second-flush", palette="bark", motif="bird", layout="story",
         headline="Malty, brisk and generous with milk",
         story="Summer in the Brahmaputra valley is hot and wet, and the tea bushes grow fast. Leaves picked "
               "now make the boldest, maltiest teas of the year.",
         rationale="Warm bark browns for a malty breakfast tea; the songbird for an early-morning cup."),
    dict(product="silver-needle", palette="buttercup", motif="butterfly", layout="wide",
         headline="Just the buds, simply dried", story="", live=True,
         rationale="Soft yellows for a pale, honeyed tea."),
]


def _item(code, name, kind, ingredient_name=""):
    return Item.objects.get_or_create(code=code, defaults=dict(name=name, kind=kind, ingredient_name=ingredient_name))[0]


def _stock(item, quantity, supplier, **fields):
    if not item.lots.exists():
        lot = Lot.objects.create(item=item, quantity_received=quantity, supplier=supplier, **fields)
        return lot
    return item.lots.first()


@transaction.atomic
def load(owner=None):
    """Create the demo catalog (skipping what already exists).  owner:
    the user recorded as approving the demo's live page design."""
    # The standard sections, in case the database was emptied since the
    # migration made them (browser tests flush it between tests).
    import importlib

    from django.apps import apps

    importlib.import_module("apps.catalog.migrations.0003_seed_sections").seed(apps, None)
    supplier = Supplier.objects.get_or_create(name="Demo Tea Importers")[0]
    best_by = date.today() + timedelta(days=540)
    regions = {}
    for order, (slug, name, country, motif, palette, intro) in enumerate(REGIONS):
        regions[slug] = Region.objects.get_or_create(
            slug=slug, defaults=dict(name=name, country=country, motif=motif, palette=palette, intro=intro,
                                     sort_order=order))[0]
    notes = {}
    for name in NOTES:
        notes[name] = FlavourNote.objects.get_or_create(slug=name.lower(), defaults={"name": name})[0]
    pouch = _item("POUCH", "Kraft pouch", Item.Kind.PACKAGING)
    tin = _item("TIN", "Tea tin", Item.Kind.PACKAGING)
    label = _item("LABEL", "Package label", Item.Kind.PACKAGING)
    for packaging in (pouch, tin, label):
        _stock(packaging, 500, supplier)
    categories = {c.slug: c for c in Category.objects.all()}
    collections = {c.slug: c for c in Collection.objects.all()}

    for order, tea in enumerate(TEAS):
        if Product.objects.filter(slug=tea["slug"]).exists():
            continue
        kind = Item.Kind.HERBAL if tea.get("kind") == "herbal" else Item.Kind.TEA
        code = tea["slug"].upper()[:20].rstrip("-")
        item = _item(code, tea["name"] + " (bulk)", kind, tea["ingredients"])
        lot = _stock(item, 4000, supplier, best_by=best_by, country_of_origin=tea["countries"],
                     ingredients=tea["ingredients"] if "," in tea["ingredients"] else "")
        if tea.get("allergens"):
            lot.allergens.set(Allergen.objects.filter(code__in=tea["allergens"]))
        temp, minutes, grams, infusions = tea["brew"]
        product = Product.objects.create(
            name=tea["name"], slug=tea["slug"], kind=Product.Kind.TEA, tea=item, label_name=tea["name"],
            category=categories.get(tea["category"]), region=regions.get(tea["region"]),
            summary=tea["summary"], origin_detail=tea.get("origin_detail", ""),
            origin_certified=tea.get("origin_certified", False), tasting_notes=tea.get("tasting_notes", ""),
            description=tea.get("description", ""), caffeine=tea["caffeine"], brew_temp_c=temp,
            brew_minutes=minutes, brew_grams=Decimal(grams), brew_infusions=infusions,
            brew_notes=tea.get("brew_notes", ""), featured=tea.get("featured", False),
        )
        Product.objects.filter(pk=product.pk).update(created_at=timezone.now() - timedelta(days=order))
        product.flavour_notes.set([notes[n] for n in tea["notes"]])
        for sort, (net, package, price) in enumerate(tea["sizes"]):
            size = SizeOption.objects.create(
                product=product, name=f"{net} g {package}", sku=f"{code[:12]}-{net}", net_grams=net,
                package=package, price=Decimal(price), sort_order=sort)
            BomLine.objects.create(size_option=size, item=tin if package == "tin" else pouch)
            BomLine.objects.create(size_option=size, item=label)
        for slug in tea.get("collections", []):
            collections[slug].products.add(product)

    for good in GOODS:
        if Product.objects.filter(slug=good["slug"]).exists():
            continue
        item = _item(good["slug"].upper()[:20], good["name"], good["kind"])
        _stock(item, 12, supplier)
        product = Product.objects.create(
            name=good["name"], slug=good["slug"], kind=Product.Kind.GOODS, category=categories.get(good["category"]),
            summary=good["summary"], description=good["description"])
        size = SizeOption.objects.create(product=product, name="Each", sku=good["slug"].upper()[:40],
                                         price=Decimal(good["price"]))
        BomLine.objects.create(size_option=size, item=item)

    for article in ARTICLES:
        if Article.objects.filter(slug=article["slug"]).exists():
            continue
        created = Article.objects.create(
            slug=article["slug"], title=article["title"], summary=article["summary"], body=article["body"],
            motif=article["motif"], palette=article["palette"], is_published=True,
            published_on=date.today() - timedelta(days=article["days_ago"]))
        created.related_products.set(Product.objects.filter(slug__in=article["products"]))

    for design in VARIANTS:
        product = Product.objects.get(slug=design["product"])
        if product.page_variants.exists():
            continue
        variant = PageVariant.objects.create(
            product=product, made_by="design-agent (demo)",
            **{k: design[k] for k in ("palette", "motif", "layout", "headline", "story", "rationale")})
        if design.get("live"):
            variant.approve(owner, "Demo design")
