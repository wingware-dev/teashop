"""Structured data (schema.org JSON-LD) that search engines read from
the shop's pages: products with their offers, breadcrumbs, the shop
itself and its search box."""

from django.conf import settings
from django.urls import reverse

from apps.catalog.models import Product

IN_STOCK = "https://schema.org/InStock"
OUT_OF_STOCK = "https://schema.org/OutOfStock"


def absolute(request, path):
    return request.build_absolute_uri(path)


def breadcrumbs(request, crumbs):
    """crumbs: [(name, path)], from the home page down."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": absolute(request, path)}
            for i, (name, path) in enumerate(crumbs, start=1)
        ],
    }


def website(request):
    home = absolute(request, reverse("storefront:home"))
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": settings.SHOP_NAME,
        "url": home,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": absolute(request, reverse("storefront:search")) + "?q={q}"},
            "query-input": "required name=q",
        },
    }


def product(request, product, sizes, photos, facts):
    """sizes: [(size, packages available)]."""
    url = absolute(request, product.get_absolute_url())
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "url": url,
        "description": product.summary or product.description[:300],
        "brand": {"@type": "Brand", "name": settings.SHOP_NAME},
        "offers": [
            {
                "@type": "Offer",
                "name": size.name,
                "sku": size.sku,
                "price": f"{size.price:.2f}",
                "priceCurrency": "USD",
                "availability": IN_STOCK if available else OUT_OF_STOCK,
                "url": url,
                "itemCondition": "https://schema.org/NewCondition",
            }
            for size, available in sizes
        ],
    }
    if sizes:
        data["sku"] = sizes[0][0].sku
    if photos:
        data["image"] = [absolute(request, photo.image.url) for photo in photos]
    if product.category_id:
        data["category"] = product.category.name
    if facts and facts["countries"]:
        data["countryOfOrigin"] = ", ".join(facts["countries"])
    properties = []
    if product.caffeine:
        properties.append({"@type": "PropertyValue", "name": "Caffeine", "value": product.get_caffeine_display()})
    if product.kind == Product.Kind.TEA and product.flavour_notes.exists():
        properties.append({"@type": "PropertyValue", "name": "Flavour notes",
                           "value": ", ".join(note.name for note in product.flavour_notes.all())})
    if properties:
        data["additionalProperty"] = properties
    return data


def article(request, article):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": article.summary,
        "datePublished": article.published_on.isoformat(),
        "dateModified": article.updated_at.date().isoformat(),
        "url": absolute(request, article.get_absolute_url()),
        "publisher": {"@type": "Organization", "name": settings.SHOP_NAME},
    }
