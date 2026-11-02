"""sitemap.xml: every page the shop shows, once it is open."""

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalog.models import Category, Collection, Region

from .browsing import shown_products
from .models import Article


class ShopSitemap(Sitemap):
    def get_urls(self, *args, **kwargs):
        if not settings.STOREFRONT_OPEN:
            return []
        return super().get_urls(*args, **kwargs)


class PagesSitemap(ShopSitemap):
    priority = 0.8

    def items(self):
        return ["storefront:home", "storefront:all_teas", "storefront:regions", "storefront:goods",
                "storefront:articles"]

    def location(self, name):
        return reverse(name)


class SectionSitemap(ShopSitemap):
    priority = 0.6

    def items(self):
        return [*Category.objects.filter(is_active=True), *Region.objects.filter(is_active=True),
                *Collection.objects.showing()]


class ProductSitemap(ShopSitemap):
    priority = 0.7

    def items(self):
        return shown_products().order_by("pk")


class ArticleSitemap(ShopSitemap):
    priority = 0.5

    def items(self):
        return Article.objects.published()

    def lastmod(self, article):
        return article.updated_at


SITEMAPS = {
    "pages": PagesSitemap,
    "sections": SectionSitemap,
    "products": ProductSitemap,
    "articles": ArticleSitemap,
}
