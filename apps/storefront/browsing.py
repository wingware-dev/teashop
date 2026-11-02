"""Which products the shop shows, and the search, filters and sorting
shared by the category, region, collection and search pages."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db.models import Min, Prefetch, Q

from apps.catalog.models import Category, FlavourNote, Product, ProductPhoto, Region, SizeOption

PAGE_SIZE = 24

SORTS = {
    "name": ("Name", ["name"]),
    "price": ("Price, low to high", ["from_price", "name"]),
    "-price": ("Price, high to low", ["-from_price", "name"]),
    "new": ("Newest first", ["-created_at", "name"]),
}


def can_see_closed_shop(user):
    """The signed-in owner sees the shop before it opens."""
    return bool(user.is_authenticated and user.is_staff and user.is_verified())


def shop_is_visible(request):
    return settings.STOREFRONT_OPEN or can_see_closed_shop(request.user)


def shown_products():
    """Active products with at least one active size, with what list
    pages need prefetched, and from_price (the cheapest active size)."""
    active_sizes = Q(size_options__is_active=True)
    return (
        Product.objects.filter(is_active=True)
        .filter(active_sizes)
        .annotate(from_price=Min("size_options__price", filter=active_sizes))
        .select_related("category", "region", "tea")
        .prefetch_related(
            "flavour_notes",
            Prefetch("photos", queryset=ProductPhoto.objects.order_by("sort_order", "pk")),
            Prefetch("size_options", queryset=SizeOption.objects.filter(is_active=True)),
        )
        .distinct()
    )


@dataclass
class Filters:
    """What the visitor asked for in the query string, cleaned."""

    q: str = ""
    categories: list = field(default_factory=list)
    regions: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    caffeine: list = field(default_factory=list)
    packages: list = field(default_factory=list)
    price_max: Decimal = None
    sort: str = "name"

    @classmethod
    def from_query(cls, params):
        def many(name, allowed=None):
            values = [v for v in params.getlist(name) if v]
            return [v for v in values if allowed is None or v in allowed][:20]

        price_max = None
        raw = params.get("price_max", "").strip().lstrip("$")
        if raw:
            try:
                price_max = Decimal(raw)
            except InvalidOperation:
                price_max = None
            if price_max is not None and (not price_max.is_finite() or price_max <= 0):
                price_max = None
        sort = params.get("sort", "name")
        return cls(
            q=params.get("q", "").strip()[:100],
            categories=many("category"),
            regions=many("region"),
            notes=many("note"),
            caffeine=many("caffeine", Product.Caffeine.values),
            packages=many("package", SizeOption.Package.values),
            price_max=price_max,
            sort=sort if sort in SORTS else "name",
        )

    @property
    def active(self):
        """True when anything narrows the list (sorting doesn't)."""
        return bool(self.q or self.categories or self.regions or self.notes or self.caffeine or self.packages
                    or self.price_max)

    def apply(self, products):
        if self.q:
            for word in self.q.split()[:8]:
                products = products.filter(
                    Q(name__icontains=word)
                    | Q(summary__icontains=word)
                    | Q(tasting_notes__icontains=word)
                    | Q(description__icontains=word)
                    | Q(origin_detail__icontains=word)
                    | Q(flavour_notes__name__icontains=word)
                    | Q(region__name__icontains=word)
                    | Q(region__country__icontains=word)
                    | Q(category__name__icontains=word)
                )
        if self.categories:
            products = products.filter(category__slug__in=self.categories)
        if self.regions:
            products = products.filter(region__slug__in=self.regions)
        for note in self.notes:  # every chosen note, not any
            products = products.filter(flavour_notes__slug=note)
        if self.caffeine:
            products = products.filter(caffeine__in=self.caffeine)
        if self.packages:
            products = products.filter(size_options__is_active=True, size_options__package__in=self.packages)
        if self.price_max:
            products = products.filter(from_price__lte=self.price_max)
        return products.order_by(*SORTS[self.sort][1]).distinct()


def filter_choices(products, fixed=()):
    """The options worth offering for products (before filtering): only
    flavour notes, regions, categories and packages some of them have.
    fixed: facets the page already fixes (e.g. "category" on a category
    page), left out."""
    ids = list(products.values_list("pk", flat=True))
    choices = {
        "notes": FlavourNote.objects.filter(products__in=ids).distinct(),
        "caffeine": [
            (value, label)
            for value, label in Product.Caffeine.choices
            if Product.objects.filter(pk__in=ids, caffeine=value).exists()
        ],
        "packages": [
            (value, label)
            for value, label in SizeOption.Package.choices
            if SizeOption.objects.filter(product__in=ids, is_active=True, package=value).exists()
        ],
        "sorts": [(key, label) for key, (label, _) in SORTS.items()],
    }
    if "category" not in fixed:
        choices["categories"] = Category.objects.filter(is_active=True, products__in=ids).distinct()
    if "region" not in fixed:
        choices["regions"] = Region.objects.filter(is_active=True, products__in=ids).distinct()
    return choices
