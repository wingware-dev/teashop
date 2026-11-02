"""The public shop: home, category, region and collection pages, search,
product pages, merch and accessories, and the tea info section.

Until the shop opens (settings.STOREFRONT_OPEN), visitors get the "coming
soon" home page and a 404 elsewhere, and only the signed-in owner sees the
rest (see browsing.shop_is_visible)."""

from functools import wraps

from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.catalog.models import Category, Collection, Product, Region

from . import seo
from .browsing import PAGE_SIZE, Filters, filter_choices, shop_is_visible, shown_products
from .models import Article


def shop_page(view):
    """Only while the shop is visible to this visitor; else a 404."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not shop_is_visible(request):
            raise Http404("The shop is not open yet")
        return view(request, *args, **kwargs)

    return require_GET(wrapper)


@require_GET
def home(request):
    if not shop_is_visible(request):
        return render(request, "storefront/coming_soon.html")
    products = shown_products()
    collections = []
    for collection in Collection.objects.showing().filter(featured=True)[:3]:
        items = list(products.filter(collections=collection).order_by("name")[:4])
        if items:
            collections.append((collection, items))
    return render(
        request,
        "storefront/home.html",
        {
            "featured": list(products.filter(featured=True).order_by("name")[:4]),
            "collections": collections,
            "tea_categories": Category.objects.filter(is_active=True, section=Category.Section.TEA),
            "regions": Region.objects.filter(is_active=True, products__is_active=True).distinct()[:8],
            "articles": Article.objects.published()[:3],
            "goods": list(products.filter(kind=Product.Kind.GOODS).order_by("name")[:4]),
            "structured_data": [seo.website(request)],
            "is_home": True,
        },
    )


def _listing(request, template, products, *, crumbs, fixed=(), context=None):
    """A page of products with the search, filter and sort form."""
    filters = Filters.from_query(request.GET)
    choices = filter_choices(products, fixed)
    page = Paginator(filters.apply(products), PAGE_SIZE).get_page(request.GET.get("page"))
    return render(
        request,
        template,
        {
            "page": page,
            "products": page.object_list,
            "filters": filters,
            "choices": choices,
            "crumbs": crumbs,
            "structured_data": [seo.breadcrumbs(request, crumbs)],
            **(context or {}),
        },
    )


HOME_CRUMB = ("Home", "/")


@shop_page
def all_teas(request):
    crumbs = [HOME_CRUMB, ("All teas", reverse("storefront:all_teas"))]
    return _listing(request, "storefront/listing.html", shown_products().filter(kind=Product.Kind.TEA),
                    crumbs=crumbs, context={"title": "All teas", "motif_name": "sprig", "palette": "moss",
                                            "intro": "Every tea and herbal tea we have, to sort and filter as you like."})


@shop_page
def category(request, slug, section):
    category = get_object_or_404(Category, slug=slug, is_active=True, section=section)
    parent = ("All teas", reverse("storefront:all_teas")) if section == Category.Section.TEA else (
        "Merch and accessories", reverse("storefront:goods"))
    crumbs = [HOME_CRUMB, parent, (category.name, category.get_absolute_url())]
    return _listing(request, "storefront/listing.html", shown_products().filter(category=category), crumbs=crumbs,
                    fixed=("category",), context={"section": category, "title": category.name,
                                                  "intro": category.intro, "motif_name": category.motif,
                                                  "palette": category.palette})


@shop_page
def region_list(request):
    regions = Region.objects.filter(is_active=True)
    by_country = {}
    for region in regions:
        by_country.setdefault(region.country, []).append(region)
    crumbs = [HOME_CRUMB, ("Regions", reverse("storefront:regions"))]
    return render(request, "storefront/regions.html",
                  {"by_country": by_country.items(), "crumbs": crumbs,
                   "structured_data": [seo.breadcrumbs(request, crumbs)]})


@shop_page
def region(request, slug):
    region = get_object_or_404(Region, slug=slug, is_active=True)
    crumbs = [HOME_CRUMB, ("Regions", reverse("storefront:regions")), (region.name, region.get_absolute_url())]
    return _listing(request, "storefront/listing.html", shown_products().filter(region=region), crumbs=crumbs,
                    fixed=("region",), context={"section": region, "title": region.name, "intro": region.intro,
                                                "kicker": region.country, "motif_name": region.motif,
                                                "palette": region.palette})


@shop_page
def collection(request, slug):
    collection = get_object_or_404(Collection.objects.showing(), slug=slug)
    crumbs = [HOME_CRUMB, (collection.name, collection.get_absolute_url())]
    return _listing(request, "storefront/listing.html", shown_products().filter(collections=collection),
                    crumbs=crumbs, context={"section": collection, "title": collection.name,
                                            "intro": collection.intro, "motif_name": collection.motif,
                                            "palette": collection.palette})


@shop_page
def search(request):
    crumbs = [HOME_CRUMB, ("Search", reverse("storefront:search"))]
    query = request.GET.get("q", "").strip()
    title = f"Search results for “{query[:100]}”" if query else "Search"
    response = _listing(request, "storefront/listing.html", shown_products(), crumbs=crumbs,
                        context={"title": title, "is_search": True, "motif_name": "bee", "palette": "buttercup"})
    return response


@shop_page
def goods(request):
    """The merch and accessories section: each category with its products."""
    categories = Category.objects.filter(is_active=True, section=Category.Section.GOODS)
    products = shown_products().filter(kind=Product.Kind.GOODS)
    sections = [(c, list(products.filter(category=c).order_by("name")[:8])) for c in categories]
    crumbs = [HOME_CRUMB, ("Merch and accessories", reverse("storefront:goods"))]
    return render(request, "storefront/goods.html",
                  {"sections": [s for s in sections if s[1]], "uncategorised": list(products.filter(category=None)),
                   "crumbs": crumbs, "structured_data": [seo.breadcrumbs(request, crumbs)]})


def product_context(request, product, variant=None):
    """What the product page shows.  variant: the design to use; default
    the product's live variant, if any."""
    if variant is None:
        variant = product.page_variants.live().first()
    sizes = [(size, size.packages_available()) for size in product.size_options.filter(is_active=True)]
    photos = list(product.photos.all())
    facts = product.shop_facts()
    if product.category_id:
        parent = (product.category.name, product.category.get_absolute_url())
    elif product.kind == Product.Kind.GOODS:
        parent = ("Merch and accessories", reverse("storefront:goods"))
    else:
        parent = ("All teas", reverse("storefront:all_teas"))
    crumbs = [HOME_CRUMB, parent, (product.name, product.get_absolute_url())]
    related = shown_products().exclude(pk=product.pk)
    if product.category_id:
        related = related.filter(category=product.category_id)
    return {
        "product": product,
        "variant": variant,
        "palette": variant.palette if variant else (product.category.palette if product.category_id else "moss"),
        "motif_name": variant.motif if variant else (product.category.motif if product.category_id else "leaf"),
        "layout": variant.layout if variant else "classic",
        "sizes": sizes,
        "in_stock_sizes": [size for size, available in sizes if available],
        "cart_max_quantity": settings.CART_MAX_QUANTITY,
        "photos": photos,
        "facts": facts,
        "related": list(related.order_by("name")[:4]),
        "articles": product.articles.published()[:3],
        "crumbs": crumbs,
        "structured_data": [seo.product(request, product, sizes, photos, facts), seo.breadcrumbs(request, crumbs)],
    }


@shop_page
def product(request, slug):
    product = (
        Product.objects.select_related("category", "region", "tea")
        .filter(slug=slug, is_active=True, size_options__is_active=True)
        .distinct()
        .first()
    )
    if product is None:
        raise Http404("No such product")
    return render(request, "storefront/product.html", product_context(request, product))


@shop_page
def article_list(request):
    crumbs = [HOME_CRUMB, ("Tea notes", reverse("storefront:articles"))]
    return render(request, "storefront/articles.html",
                  {"articles": Article.objects.published(), "crumbs": crumbs,
                   "structured_data": [seo.breadcrumbs(request, crumbs)]})


@shop_page
def article(request, slug):
    article = get_object_or_404(Article.objects.published(), slug=slug)
    crumbs = [HOME_CRUMB, ("Tea notes", reverse("storefront:articles")), (article.title, article.get_absolute_url())]
    return render(request, "storefront/article.html",
                  {"article": article, "related": shown_products().filter(articles=article)[:4], "crumbs": crumbs,
                   "structured_data": [seo.article(request, article), seo.breadcrumbs(request, crumbs)]})


@require_GET
def policy(request, slug):
    """A policy page.  Shown even while the shop is closed: the terms and
    the privacy policy must be reachable whenever anyone can be a
    customer (including a subscriber cancelling)."""
    from . import policies

    if slug not in policies.POLICIES:
        raise Http404("No such policy")
    crumbs = [HOME_CRUMB, (policies.POLICIES[slug], reverse("storefront:policy", args=[slug]))]
    return render(request, f"storefront/policies/{slug}.html", {
        "title": policies.POLICIES[slug], "updated": policies.UPDATED, "processors": policies.PROCESSORS,
        "policies": policies.POLICIES, "crumbs": crumbs, "checkout": _checkout_facts(),
    })


def _checkout_facts():
    """What the policies quote from the checkout settings."""
    from apps.checkout.models import CheckoutSettings

    shop = CheckoutSettings.current()
    return {"ship_within_days": shop.ship_within_days, "free_shipping_over": shop.free_shipping_over,
            "postal_address": settings.SHOP_POSTAL_ADDRESS, "contact_email": settings.SHOP_CONTACT_EMAIL,
            "state": settings.SHOP_STATE}


@require_GET
def robots_txt(request):
    if settings.STOREFRONT_OPEN:
        lines = [
            "User-agent: *",
            "Disallow: /owner/",
            "Disallow: /account/",
            "Disallow: /your-account/",
            "Disallow: /cart/",
            "Disallow: /checkout/",
            "Disallow: /orders/",
            "Disallow: /subscriptions/pay/",
            "Disallow: /subscriptions/cancel/",
            "Disallow: /subscriptions/welcome/",
            # Not the admin's path: it is kept out of sight on purpose.
            "Disallow: /search/",
            "",
            f"Sitemap: {request.build_absolute_uri(reverse('storefront:sitemap'))}",
        ]
    else:
        # Not open yet: keep the coming-soon site out of search results.
        lines = ["User-agent: *", "Disallow: /"]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")
